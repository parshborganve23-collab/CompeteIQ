"""CompeteIQ BAND worker with real Ollama LLM reasoning."""

import asyncio
import json
import logging
import os
import sys
from typing import Any

import httpx

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from band import Agent
from band.adapters import LangGraphAdapter
from band.runtime.formatters import strip_leading_mentions
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, MessagesState, StateGraph

from integrations.band import BAND_AGENT_DEFS, _agent_env, band_integration


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("competeiq-band-worker")

OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL", "http://localhost:11434/v1"
).rstrip("/")

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:3b")

OLLAMA_TIMEOUT = float(os.getenv("OLLAMA_TIMEOUT", "120"))


async def ask_ollama(system_prompt: str, user_prompt: str) -> str:
    """Generate a genuine LLM response using the local Ollama model."""

    payload = {
        "model": OLLAMA_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.2,
        "stream": False,
    }

    async with httpx.AsyncClient(timeout=OLLAMA_TIMEOUT) as client:
        response = await client.post(
            f"{OLLAMA_BASE_URL}/chat/completions",
            json=payload,
        )
        response.raise_for_status()

    result = response.json()
    content = result["choices"][0]["message"]["content"].strip()

    if not content:
        raise ValueError("Ollama returned an empty response.")

    return content


def build_agent_adapter(
    agent_name: str,
    agent_role: str,
    agent_task: str,
    handoff_to: str,
    own_agent_id: str = "",
):
    """Build a LangGraph adapter for one BAND agent."""

    checkpointer = InMemorySaver()

    def graph_factory(band_tools: list[Any]):
        send_message = next(
            (tool for tool in band_tools if tool.name == "band_send_message"),
            None,
        )

        async def reply(state: MessagesState) -> dict[str, list[Any]]:
            if not state["messages"]:
                return {"messages": []}

            content = str(state["messages"][-1].content)

            # BAND provides incoming messages as JSON records.
            records = []

            for line in content.splitlines():
                line = line.strip()

                if not line.startswith("{"):
                    continue

                try:
                    record = json.loads(line)
                except json.JSONDecodeError:
                    continue

                if (
                    isinstance(record, dict)
                    and record.get("sender_id")
                    and record.get("content") is not None
                ):
                    records.append(record)

            if not records:
                logger.warning(
                    "[%s] No valid incoming BAND messages.",
                    agent_name,
                )
                return {"messages": []}

            mentions = []
            message_lines = []
            task_records = []
            peer_reply_records = []

            for record in records:
                sender_id = str(record["sender_id"]).strip()
                sender_name = str(
                    record.get("sender_name") or "Participant"
                )

                incoming_text = strip_leading_mentions(
                    str(record.get("content") or "")
                ).strip()

                if not incoming_text:
                    continue

                message_lines.append(
                    f"Message from {sender_name}:\n{incoming_text}"
                )

                first_line = incoming_text.split("\n", 1)[0]

                # Other agents' replies are findings, not new task dispatches.
                if first_line.startswith("Agent: "):
                    peer_reply_records.append(record)
                else:
                    task_records.append(record)

                    if (
                        sender_id
                        and sender_id != own_agent_id
                        and sender_id not in mentions
                    ):
                        mentions.append(sender_id)

            async def settle_no_reply(reason: str):
                no_reply_tool = next(
                    (
                        tool for tool in band_tools
                        if tool.name == "band_no_reply"
                    ),
                    None,
                )

                if no_reply_tool:
                    logger.info("[%s] %s", agent_name, reason)
                    await no_reply_tool.ainvoke({"reason": reason})

            if not task_records:
                # Strategy Agent consolidates findings from the other agents.
                if (
                    agent_name == "Strategy Agent"
                    and peer_reply_records
                ):
                    if not send_message:
                        logger.error(
                            "[%s] BAND send_message tool unavailable.",
                            agent_name,
                        )
                        return {"messages": []}

                    syn_mentions = []

                    for record in peer_reply_records:
                        sender_id = str(record["sender_id"]).strip()

                        if (
                            sender_id
                            and sender_id != own_agent_id
                            and sender_id not in syn_mentions
                        ):
                            syn_mentions.append(sender_id)

                    if not syn_mentions:
                        await settle_no_reply(
                            "No participants available for strategy synthesis."
                        )
                        return {"messages": []}

                    findings = "\n\n".join(message_lines)

                    system_prompt = """
You are the Strategy Intelligence Agent of CompeteIQ,
an AI competitive intelligence platform developed by NEXORA AI.

Your responsibility is to combine findings from specialist agents
into one practical, evidence-based strategic recommendation.

Think critically. Identify agreements, disagreements, opportunities,
risks, business impact, and missing evidence.

Do not invent facts, numbers, sources, or financial results.
Clearly distinguish facts from assumptions.
"""

                    user_prompt = f"""
Prepare the final strategic recommendation for NEXORA AI.

Specialist agent findings:
{findings}

Produce the following sections:

1. Executive Summary
2. Key Findings
3. Competitive Threats
4. Market and Product Opportunities
5. Financial Implications
6. Risk Assessment
7. Recommended Actions
8. Short-term and Long-term Strategy
9. Metrics to Monitor

Prioritize actions and explain why each action matters.
"""

                    try:
                        logger.info(
                            "[%s] Generating final strategy with Ollama (%s).",
                            agent_name,
                            OLLAMA_MODEL,
                        )

                        strategy = await ask_ollama(
                            system_prompt,
                            user_prompt,
                        )

                    except Exception:
                        logger.exception(
                            "[%s] Ollama strategy generation failed.",
                            agent_name,
                        )
                        await settle_no_reply(
                            "LLM strategy generation failed; no fabricated response sent."
                        )
                        return {"messages": []}

                    final_message = (
                        f"Agent: {agent_name}\n"
                        f"Role: {agent_role}\n\n"
                        f"FINAL STRATEGIC RECOMMENDATION FOR NEXORA AI\n\n"
                        f"{strategy}"
                    )

                    await send_message.ainvoke(
                        {
                            "content": final_message,
                            "mentions": syn_mentions,
                        }
                    )

                    logger.info(
                        "[%s] Real LLM strategy sent to %d participant(s).",
                        agent_name,
                        len(syn_mentions),
                    )

                    return {"messages": []}

                await settle_no_reply(
                    "Peer-agent replies only; avoiding a reply loop."
                )
                return {"messages": []}

            if not mentions:
                await settle_no_reply(
                    "No valid external participant to mention."
                )
                return {"messages": []}

            if not send_message:
                logger.error(
                    "[%s] BAND send_message tool unavailable.",
                    agent_name,
                )
                return {"messages": []}

            task_lines = [
                line
                for line in message_lines
                if not line.split("\n", 1)[-1].startswith("Agent: ")
            ]

            task_context = "\n\n".join(task_lines or message_lines)

            system_prompt = f"""
You are the {agent_name} of CompeteIQ,
an AI competitive intelligence platform developed by NEXORA AI.

Your specialist role:
{agent_role}

Your assigned responsibility:
{agent_task}

Analyze the task using careful reasoning.
Give specific, useful business intelligence.
Explain evidence, implications, opportunities, and risks.

Do not invent facts, sources, statistics, or financial figures.
If information is missing, clearly say what needs verification.
Do not simply repeat the task.
"""

            user_prompt = f"""
Analyze this competitive intelligence task.

Task and event context:
{task_context}

Return your findings in this structure:

1. What happened?
2. Important findings
3. Evidence and information available
4. Impact on NEXORA AI
5. Opportunities
6. Risks and threats
7. Recommended actions
8. Information that still needs verification

Focus on your specialist role. Be clear and practical.
"""

            try:
                logger.info(
                    "[%s] Generating real LLM analysis using %s.",
                    agent_name,
                    OLLAMA_MODEL,
                )

                reasoning = await ask_ollama(
                    system_prompt,
                    user_prompt,
                )

            except Exception:
                logger.exception(
                    "[%s] Ollama analysis generation failed.",
                    agent_name,
                )
                await settle_no_reply(
                    "LLM analysis failed; no fabricated response sent."
                )
                return {"messages": []}

            agent_message = (
                f"Agent: {agent_name}\n"
                f"Role: {agent_role}\n\n"
                f"{reasoning}"
            )

            if handoff_to:
                agent_message += (
                    f"\n\nNext agent in chain: {handoff_to}"
                )

            await send_message.ainvoke(
                {
                    "content": agent_message,
                    "mentions": mentions,
                }
            )

            logger.info(
                "[%s] Real LLM analysis sent to %d participant(s).",
                agent_name,
                len(mentions),
            )

            return {"messages": []}

        builder = StateGraph(MessagesState)
        builder.add_node("reply", reply)
        builder.add_edge(START, "reply")
        builder.add_edge("reply", END)

        return builder.compile(checkpointer=checkpointer)

    return LangGraphAdapter(graph_factory=graph_factory)


async def run_single_agent(adef: dict) -> None:
    """Create and run one persistent BAND agent."""

    key = adef["key"]
    agent_id, agent_key = _agent_env(key)

    if not agent_id or not agent_key:
        logger.warning(
            "Skipping %s: missing BAND credentials.",
            adef["name"],
        )
        return

    logger.info("Creating BAND agent: %s", adef["name"])

    adapter = build_agent_adapter(
        agent_name=adef["name"],
        agent_role=adef["role"],
        agent_task=adef["task"],
        handoff_to="",
        own_agent_id=agent_id,
    )

    try:
        agent = Agent.create(
            adapter=adapter,
            agent_id=agent_id,
            api_key=agent_key,
            rest_url=band_integration.api_url,
        )

        logger.info(
            "Agent %s connected to BAND Cloud.",
            adef["name"],
        )

        await agent.run()

    except Exception:
        logger.exception("Agent %s failed.", adef["name"])


async def main() -> None:
    """Run all configured CompeteIQ agents."""

    logger.info("Starting CompeteIQ BAND AI worker...")
    logger.info("Configured agents: %d", len(BAND_AGENT_DEFS))
    logger.info("Ollama model: %s", OLLAMA_MODEL)
    logger.info("Ollama endpoint: %s", OLLAMA_BASE_URL)

    configured_agents = []

    for adef in BAND_AGENT_DEFS:
        agent_id, agent_key = _agent_env(adef["key"])

        if agent_id and agent_key:
            configured_agents.append(adef)
        else:
            logger.warning(
                "Agent %s is not configured.",
                adef["name"],
            )

    logger.info(
        "Agents with credentials: %d/%d",
        len(configured_agents),
        len(BAND_AGENT_DEFS),
    )

    if not configured_agents:
        logger.error("No BAND agents configured. Exiting.")
        sys.exit(1)

    await asyncio.gather(
        *(run_single_agent(adef) for adef in configured_agents)
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("BAND AI worker stopped by user.")
        sys.exit(0)