"""BAND AI multi-agent integration — real SDK integration.

Uses the official band-sdk Python SDK (8.1.0). Each of the seven CompeteIQ
agents is a separately registered Band remote agent with its own agent ID and
agent API key. Every REST call authenticates as that agent with its own key
(the ``X-API-Key`` header) against the Band Agent API.

The documented REST base is ``https://app.band.ai/api/v1``. The Python SDK
appends ``/api/v1`` to the configured base URL, so ``RestClient`` and
``Agent.create(rest_url=...)`` are given ``https://app.band.ai``.

Official docs:
  https://docs.band.ai/security/authentication
  https://docs.band.ai/quickstart
"""
import logging
import os
import re
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from band.client.rest import (
    DEFAULT_REQUEST_OPTIONS,
    ChatMessageRequest,
    ChatMessageRequestMentionsItem,
    ChatRoomRequest,
    ParticipantRequest,
    RestClient,
)
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load backend/.env regardless of the process working directory.
load_dotenv(Path(__file__).resolve().parent.parent / ".env")

# Documented Band REST base. The SDK appends "/api/v1" itself.
DOCUMENTED_REST_BASE = "https://app.band.ai/api/v1"
DEFAULT_SDK_BASE_URL = "https://app.band.ai"


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class BandStatus:
    configured: bool
    available: bool
    reason: str
    agents: List[dict] = field(default_factory=list)
    setup_instructions: List[str] = field(default_factory=list)
    authenticated_count: int = 0
    configured_count: int = 0
    rest_base: str = DOCUMENTED_REST_BASE


# The seven specialized CompeteIQ BAND AI agents
BAND_AGENT_DEFS = [
    {
        "key": "research",
        "name": "Research Agent",
        "role": "Competitor evidence gathering",
        "task": "Investigate the trending event and collect evidence about the competitor's move.",
    },
    {
        "key": "product",
        "name": "Product Intelligence Agent",
        "role": "Model & product comparison",
        "task": "Evaluate competitor models and products against NEXORA AI capabilities.",
    },
    {
        "key": "market",
        "name": "Market Intelligence Agent",
        "role": "Market positioning",
        "task": "Examine how the event affects market positioning for NEXORA AI and MINTY-GPT.",
    },
    {
        "key": "financial",
        "name": "Financial Intelligence Agent",
        "role": "Pricing & financial analysis",
        "task": "Evaluate pricing changes and financial implications of the event.",
    },
    {
        "key": "historical",
        "name": "Historical Intelligence Agent",
        "role": "Historical context",
        "task": "Retrieve historical context from Hindsight memory when available.",
    },
    {
        "key": "risk",
        "name": "Risk Analysis Agent",
        "role": "Assumption & threat checking",
        "task": "Check agent findings for assumptions, gaps, and threats.",
    },
    {
        "key": "strategy",
        "name": "Strategy Agent",
        "role": "Final recommendation",
        "task": "Synthesize all agent outputs into the final strategic recommendation.",
    },
]

# Order used when choosing which authenticated agent dispatches a message.
_SENDER_ORDER = ["strategy", "research", "product", "market", "financial", "historical", "risk"]


def _agent_env(key: str) -> tuple[str, str]:
    """Read agent_id and api_key from environment variables for a given agent key."""
    prefix = f"BAND_AGENT_{key.upper()}"
    agent_id = os.getenv(f"{prefix}_ID", "").strip()
    api_key = os.getenv(f"{prefix}_KEY", "").strip()
    return agent_id, api_key


class BandIntegration:
    """Wrapper around the official band-sdk Python SDK.

    Authentication is per agent. ``initialize()`` creates one ``RestClient``
    per configured agent and validates it with ``GET /api/v1/agent/me``. The
    legacy ``BAND_AI_API_KEY`` is deliberately not required.
    """

    # Revalidate agent credentials after this many seconds.
    STATUS_CACHE_SECONDS = 30.0

    # Pause between workflow dispatches to stay under Band rate limits.
    DISPATCH_STAGGER_SECONDS = 0.25
    DISPATCH_RETRY_DELAY_SECONDS = 1.0

    def __init__(self):
        self.api_url: str = self._normalize_base_url(
            os.getenv("BAND_AI_API_URL") or os.getenv("BAND_REST_URL")
        )
        # Legacy value kept for backwards compatibility; never used as the
        # credential for per-agent operations.
        self.api_key: Optional[str] = os.getenv("BAND_AI_API_KEY") or None
        self.timeout: float = float(os.getenv("BAND_TIMEOUT_SECONDS", "15"))

        # First authenticated client (legacy attribute used by older code).
        self.rest_client: Optional[RestClient] = None

        self._clients: Dict[str, RestClient] = {}
        self._agent_states: Dict[str, dict] = {}
        self._signature: tuple = ()
        self._initialized: bool = False
        self._available: bool = False
        self._last_attempt: float = 0.0
        self._lock = threading.Lock()
        self._setup_instructions: List[str] = []
        self._room_id: Optional[str] = None
        self._room_warnings: List[str] = []
        self._participants: set = set()
        self._participant_errors: Dict[str, str] = {}

    # ---------- helpers ----------

    @staticmethod
    def _normalize_base_url(url: Optional[str]) -> str:
        """Return the SDK base URL (without the trailing /api/v1).

        The documented REST base is https://app.band.ai/api/v1, but the SDK
        already appends /api/v1 to its base URL.
        """
        base = (url or DEFAULT_SDK_BASE_URL).strip().rstrip("/")
        if base.endswith("/api/v1"):
            base = base[: -len("/api/v1")].rstrip("/")
        return base or DEFAULT_SDK_BASE_URL

    def _credentials(self) -> Dict[str, tuple]:
        return {adef["key"]: _agent_env(adef["key"]) for adef in BAND_AGENT_DEFS}

    def _signature_for(self, credentials: Dict[str, tuple]) -> tuple:
        return tuple(
            (key, agent_id, api_key)
            for key in sorted(credentials)
            for agent_id, api_key in [credentials[key]]
        )

    def _all_keys(self) -> List[str]:
        return [key for _, key in self._credentials().values() if key]

    def _sanitize(self, value: Any) -> str:
        text = str(value)
        for key in self._all_keys():
            text = text.replace(key, "***")
        return text

    def _friendly_error(self, exc: Exception) -> str:
        """Return a short, credential-free description of an API error."""
        text = self._sanitize(exc)

        # Fern SDK errors expose the response body as ``.body``.
        body = getattr(exc, "body", None)
        if isinstance(body, dict):
            err = body.get("error") or {}
            if isinstance(err, dict) and err.get("message"):
                return str(err["message"])

        match = re.search(r"message='([^']+)'", text)
        if match:
            return match.group(1)
        if "status_code: 401" in text:
            return "401 Unauthorized: invalid or revoked agent API key"
        if "status_code: 403" in text:
            return "403 Forbidden: this credential is not allowed on the Agent API"
        return text[:300]

    def _public_state(self, state: dict) -> dict:
        return {
            "key": state["key"],
            "name": state["name"],
            "role": state["role"],
            "configured": state["configured"],
            "authenticated": state["authenticated"],
            "agent_id": state["agent_id"],
            "remote_id": state["remote_id"],
            "remote_name": state["remote_name"],
            "handle": state["handle"],
            "error": state["error"],
        }

    # ---------- initialization ----------

    def initialize(self, force: bool = False) -> bool:
        """Authenticate every configured agent against the Band Agent API.

        Results are cached for ``STATUS_CACHE_SECONDS``; pass ``force=True``
        to revalidate immediately. This method never raises: failure details
        are captured in each agent's state and in the returned availability.
        """
        credentials = self._credentials()
        signature = self._signature_for(credentials)

        with self._lock:
            now = time.monotonic()
            if (
                not force
                and self._initialized
                and self._signature == signature
                and (now - self._last_attempt) < self.STATUS_CACHE_SECONDS
            ):
                return self._available

            # Credentials changed: the old chat may belong to different agents.
            if self._signature and self._signature != signature:
                self._room_id = None
                self._participants = set()
                self._participant_errors = {}
                self._room_warnings = []

            states: Dict[str, dict] = {}
            clients: Dict[str, RestClient] = {}
            configured_count = 0
            authenticated_count = 0

            for adef in BAND_AGENT_DEFS:
                agent_id, api_key = credentials[adef["key"]]
                state = {
                    "key": adef["key"],
                    "name": adef["name"],
                    "role": adef["role"],
                    "configured": bool(agent_id and api_key),
                    "authenticated": False,
                    "agent_id": agent_id,
                    "remote_id": "",
                    "remote_name": "",
                    "handle": "",
                    "error": None,
                }

                if not agent_id or not api_key:
                    state["error"] = (
                        f"Set BAND_AGENT_{adef['key'].upper()}_ID and "
                        f"BAND_AGENT_{adef['key'].upper()}_KEY"
                    )
                    states[adef["key"]] = state
                    continue

                configured_count += 1
                try:
                    client = RestClient(
                        base_url=self.api_url,
                        api_key=api_key,
                        timeout=self.timeout,
                    )
                    # Real identity check: 200 means the agent key is valid.
                    me = client.agent_api_identity.get_agent_me(
                        request_options=DEFAULT_REQUEST_OPTIONS
                    )
                    me_data = getattr(me, "data", me)
                    state["authenticated"] = True
                    state["remote_id"] = getattr(me_data, "id", "") or ""
                    state["remote_name"] = getattr(me_data, "name", "") or ""
                    state["handle"] = getattr(me_data, "handle", "") or ""

                    if agent_id and state["remote_id"] and state["remote_id"] != agent_id:
                        state["error"] = (
                            "Agent API key is valid but belongs to agent "
                            f"{state['remote_id']}, not the configured ID {agent_id}. "
                            "Using the authenticated identity."
                        )
                    clients[adef["key"]] = client
                    authenticated_count += 1
                except Exception as exc:  # noqa: BLE001
                    state["error"] = self._friendly_error(exc)
                    logger.warning(
                        "BAND agent %s authentication failed: %s",
                        adef["name"],
                        state["error"],
                    )

                states[adef["key"]] = state

            self._agent_states = states
            self._clients = clients
            self._signature = signature
            self._initialized = True
            self._last_attempt = now
            self._available = authenticated_count > 0
            self.rest_client = next(iter(clients.values()), None)

            if configured_count == 0:
                self._setup_instructions = [
                    "BAND AI is not configured for per-agent authentication.",
                    "1. Create a Band account at https://app.band.ai",
                    "2. Register the 7 CompeteIQ agents (Agents > Connect remote agent):",
                    "   Research, Product Intelligence, Market Intelligence, Financial",
                    "   Intelligence, Historical Intelligence, Risk Analysis, Strategy",
                    "3. Copy each agent's ID and Agent API key from the creation dialog.",
                    "4. Set BAND_AGENT_<KEY>_ID and BAND_AGENT_<KEY>_KEY in backend/.env",
                    "   for RESEARCH, PRODUCT, MARKET, FINANCIAL, HISTORICAL, RISK, STRATEGY.",
                    "5. Run backend/band_worker.py to connect the persistent agents.",
                    "6. Restart the CompeteIQ backend.",
                ]
            elif authenticated_count == 0:
                self._setup_instructions = [
                    "BAND agent credentials were found but authentication failed.",
                    "Verify each BAND_AGENT_<KEY>_ID / BAND_AGENT_<KEY>_KEY pair.",
                    "The key must be an agent API key (band_a_...), not a user API key.",
                    "Check the agent has not been deleted and its key was not regenerated.",
                    "Then restart the CompeteIQ backend.",
                ]
            elif authenticated_count < len(BAND_AGENT_DEFS):
                failed = [
                    f"{s['name']}: {s['error']}"
                    for s in states.values()
                    if not s["authenticated"]
                ]
                self._setup_instructions = [
                    f"{authenticated_count}/{len(BAND_AGENT_DEFS)} BAND agents authenticated.",
                    "Fix the following agents to complete the workflow:",
                    *failed,
                ]
            else:
                self._setup_instructions = []

            logger.info(
                "BAND AI initialized: %s/%s agents authenticated (base=%s)",
                authenticated_count,
                len(BAND_AGENT_DEFS),
                self.api_url,
            )
            return self._available

    # ---------- status ----------

    def is_configured(self) -> bool:
        return any(agent_id and api_key for agent_id, api_key in self._credentials().values())

    def is_available(self) -> bool:
        self.initialize()
        return self._available

    def status(self) -> BandStatus:
        self.initialize()

        states = [self._public_state(s) for s in self._agent_states.values()]
        configured_count = sum(1 for s in states if s["configured"])
        authenticated_count = sum(1 for s in states if s["authenticated"])

        if configured_count == 0:
            return BandStatus(
                configured=False,
                available=False,
                reason=(
                    "No per-agent BAND credentials configured. "
                    "Set BAND_AGENT_<KEY>_ID and BAND_AGENT_<KEY>_KEY."
                ),
                agents=states,
                setup_instructions=self._setup_instructions,
                configured_count=0,
                rest_base=DOCUMENTED_REST_BASE,
            )

        if authenticated_count == 0:
            first_error = next(
                (s["error"] for s in states if s["configured"] and s["error"]),
                "authentication failed",
            )
            return BandStatus(
                configured=True,
                available=False,
                reason=f"0/{configured_count} configured BAND agents authenticated: {first_error}",
                agents=states,
                setup_instructions=self._setup_instructions,
                configured_count=configured_count,
                rest_base=DOCUMENTED_REST_BASE,
            )

        if authenticated_count < len(BAND_AGENT_DEFS):
            reason = (
                f"{authenticated_count}/{len(BAND_AGENT_DEFS)} BAND agents authenticated "
                "(partial workflow availability)"
            )
        else:
            reason = f"All {authenticated_count} BAND agents authenticated"

        return BandStatus(
            configured=True,
            available=True,
            reason=reason,
            agents=states,
            setup_instructions=self._setup_instructions,
            authenticated_count=authenticated_count,
            configured_count=configured_count,
            rest_base=DOCUMENTED_REST_BASE,
        )

    def list_agents(self) -> List[dict]:
        """Return the seven agents with their real authentication state."""
        self.initialize()
        return [self._public_state(s) for s in self._agent_states.values()]

    # ---------- agent creation for persistent workers ----------

    def create_agent(self, agent_key: str, adapter) -> Optional[Any]:
        """Create a Band Agent instance using Agent.create() with real credentials.

        Returns an Agent instance ready for .run() (blocking, meant for a
        separate process). Returns None if the agent is not configured.
        """
        from band import Agent

        agent_id, agent_key_val = _agent_env(agent_key)
        if not agent_id or not agent_key_val:
            return None

        try:
            return Agent.create(
                adapter=adapter,
                agent_id=agent_id,
                api_key=agent_key_val,
                rest_url=self.api_url,
            )
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(
                f"Failed to create Band agent '{agent_key}': {self._friendly_error(exc)}"
            ) from exc

    # ---------- real Band AI operations via the Agent API ----------

    def _require_available(self):
        if not self.is_available():
            status = self.status()
            raise RuntimeError(f"BAND AI is not available. {status.reason}")

    def _resolve_agent(self, name_or_key: Optional[str]) -> Optional[dict]:
        if not name_or_key:
            return None
        needle = name_or_key.strip().lower()
        for state in self._agent_states.values():
            candidates = {
                state["key"].lower(),
                state["name"].lower(),
                state["handle"].lower(),
                state["remote_id"].lower(),
            }
            if needle in candidates:
                return state
        return None

    def _sender_for(self, target_key: str) -> Optional[str]:
        def usable(key: str) -> bool:
            if key not in self._clients:
                return False
            # Once a chat exists, the sender must be a participant in it.
            return not self._room_id or key in self._participants

        for key in _SENDER_ORDER:
            if key != target_key and usable(key):
                return key
        # Only one agent is authenticated/participating: allow self-addressing.
        if usable(target_key):
            return target_key
        return None

    def _ensure_room(self, room_id: Optional[str] = None, title: Optional[str] = None) -> str:
        """Reuse a stored room reference or create a real Band chat once.

        When ``room_id`` is supplied (a previously persisted room reference),
        the existing room is validated with a real GET /agent/chats/{id} call
        and reused so repeated workflow runs never create duplicate rooms.
        Otherwise a fresh chat is created and all authenticated agents are
        added by the room owner.
        """
        if room_id:
            owner_key = next((k for k in _SENDER_ORDER if k in self._clients), None)
            if not owner_key:
                raise RuntimeError(
                    "No authenticated BAND agent is available to validate the chat."
                )
            owner = self._clients[owner_key]
            try:
                owner.agent_api_chats.get_agent_chat(room_id)
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "Stored BAND room %s is no longer reachable (%s); creating a new room.",
                    room_id,
                    self._friendly_error(exc),
                )
            else:
                # Reused room: verify the participants still exist (real API)
                # and add any missing ones so sender selection keeps working.
                self._room_id = room_id
                self._room_warnings = []
                self._participant_errors = {}
                participant_ids = set()
                try:
                    listing = owner.agent_api_participants.list_agent_chat_participants(
                        room_id,
                        request_options=DEFAULT_REQUEST_OPTIONS,
                    )
                    plist = getattr(listing, "data", None) or []
                    for p in plist:
                        pid = getattr(p, "id", "") or ""
                        if pid:
                            participant_ids.add(pid)
                    self._participants = set()
                    for key, state in self._agent_states.items():
                        if state["remote_id"] in participant_ids:
                            self._participants.add(key)
                except Exception as exc:  # noqa: BLE001
                    logger.warning(
                        "Could not list participants of BAND room %s: %s",
                        room_id,
                        self._friendly_error(exc),
                    )
                    self._participants = set(self._agent_states.keys())
                    participant_ids = {s["remote_id"] for s in self._agent_states.values()}
                for key in self._clients:
                    state = self._agent_states[key]
                    if state["remote_id"] in participant_ids:
                        continue
                    try:
                        owner.agent_api_participants.add_agent_chat_participant(
                            room_id,
                            participant=ParticipantRequest(participant_id=state["remote_id"]),
                            request_options=DEFAULT_REQUEST_OPTIONS,
                        )
                        self._participants.add(key)
                        participant_ids.add(state["remote_id"])
                    except Exception as exc:  # noqa: BLE001
                        warning = self._friendly_error(exc)
                        self._participant_errors[key] = warning
                        self._room_warnings.append(f"{state['name']}: {warning}")
                        logger.warning(
                            "Could not re-add %s to BAND room %s: %s",
                            state["name"],
                            room_id,
                            warning,
                        )
                return room_id

        owner_key = next((k for k in _SENDER_ORDER if k in self._clients), None)
        if not owner_key:
            raise RuntimeError("No authenticated BAND agent is available to create a chat.")

        owner = self._clients[owner_key]
        try:
            response = owner.agent_api_chats.create_agent_chat(
                chat=ChatRoomRequest(
                    title=title or "CompeteIQ Agent Collaboration"
                ),
                request_options=DEFAULT_REQUEST_OPTIONS,
            )
            room_id = response.data.id
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(
                f"BAND chat creation failed: {self._friendly_error(exc)}"
            ) from exc

        self._room_warnings = []
        self._participants = {owner_key}
        self._participant_errors = {}
        for key in self._clients:
            if key == owner_key:
                continue
            state = self._agent_states[key]
            try:
                # The room owner adds every participant; the target agent's
                # own client cannot see the room until it has joined.
                owner.agent_api_participants.add_agent_chat_participant(
                    room_id,
                    participant=ParticipantRequest(participant_id=state["remote_id"]),
                    request_options=DEFAULT_REQUEST_OPTIONS,
                )
                self._participants.add(key)
            except Exception as exc:  # noqa: BLE001
                warning = self._friendly_error(exc)
                self._participant_errors[key] = warning
                self._room_warnings.append(f"{state['name']}: {warning}")
                logger.warning(
                    "Could not add %s to BAND chat %s: %s",
                    state["name"],
                    room_id,
                    warning,
                )

        self._room_id = room_id
        return room_id

    def _send_to_agent(
        self,
        sender_key: str,
        target_key: str,
        content: str,
        extra_mentions: Optional[List[str]] = None,
    ) -> dict:
        room_id = self._ensure_room()
        if target_key not in self._participants:
            error = self._participant_errors.get(target_key, "not a chat participant")
            raise RuntimeError(
                f"BAND agent '{self._agent_states[target_key]['name']}' "
                f"could not join the Band chat: {error}"
            )

        sender = self._clients[sender_key]
        target = self._agent_states[target_key]

        mentions = [
            ChatMessageRequestMentionsItem(
                id=target["remote_id"],
                name=target["remote_name"] or target["name"],
                kind="mention",
            )
        ]
        sender_id = self._agent_states[sender_key].get("remote_id")
        for key in extra_mentions or []:
            extra = self._agent_states.get(key)
            if not extra or not extra["authenticated"]:
                continue
            if sender_id and extra["remote_id"] == sender_id:
                # Band rejects 422 cannot_mention_self: the sender never
                # mentions itself (e.g. handing off to the next agent when
                # the sender already IS that agent).
                continue
            mentions.append(
                ChatMessageRequestMentionsItem(
                    id=extra["remote_id"],
                    name=extra["remote_name"] or extra["name"],
                    kind="mention",
                )
            )

        try:
            response = sender.agent_api_messages.create_agent_chat_message(
                room_id,
                message=ChatMessageRequest(content=content, mentions=mentions),
                request_options=DEFAULT_REQUEST_OPTIONS,
            )
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(
                f"BAND message send failed: {self._friendly_error(exc)}"
            ) from exc

        data = response.data
        return {
            "chat_id": room_id,
            "message_id": getattr(data, "id", "") or "",
            "success": bool(getattr(data, "success", False)),
            "recipients": [
                {
                    "id": getattr(r, "id", "") or "",
                    "name": getattr(r, "name", None),
                    "handle": getattr(r, "handle", ""),
                }
                for r in (getattr(data, "recipients", None) or [])
            ],
        }

    def publish_room_message(self, room_id: str, content: str) -> dict:
        """Broadcast a text message to the room as the room owner.

        Used for the original event publication, handoff-independent
        announcements, and the final workflow completion summary. A mention
        of the first authenticated non-owner agent keeps routing valid (Band
        requires at least one mention and rejects self-mentions).
        """
        owner_key = next((k for k in _SENDER_ORDER if k in self._clients), None)
        if not owner_key:
            raise RuntimeError("No authenticated BAND agent is available to post.")
        sender = self._clients[owner_key]
        owner_id = self._agent_states[owner_key].get("remote_id", "")

        mentions = []
        for key in _SENDER_ORDER[1:]:
            state = self._agent_states.get(key)
            if (
                state
                and state["authenticated"]
                and state.get("remote_id")
                and state["remote_id"] != owner_id
            ):
                mentions.append(
                    ChatMessageRequestMentionsItem(
                        id=state["remote_id"],
                        name=state["remote_name"] or state["name"],
                        kind="mention",
                    )
                )
        try:
            response = sender.agent_api_messages.create_agent_chat_message(
                room_id,
                message=ChatMessageRequest(content=content, mentions=mentions),
                request_options=DEFAULT_REQUEST_OPTIONS,
            )
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(
                f"BAND room message failed: {self._friendly_error(exc)}"
            ) from exc
        data = response.data
        return {
            "chat_id": room_id,
            "message_id": getattr(data, "id", "") or "",
            "sender": self._agent_states[owner_key]["name"],
            "success": bool(getattr(data, "success", False)),
            "recipients": [
                {
                    "id": getattr(r, "id", "") or "",
                    "name": getattr(r, "name", None),
                    "handle": getattr(r, "handle", ""),
                }
                for r in (getattr(data, "recipients", None) or [])
            ],
        }

    @staticmethod
    def _transcript_from_message(m: Any) -> dict:
        """Extract the real room transcript fields from a ChatMessage."""
        return {
            "id": getattr(m, "id", "") or "",
            "sender_id": getattr(m, "sender_id", "") or "",
            "sender_name": getattr(m, "sender_name", "") or "",
            "sender_type": getattr(m, "sender_type", "") or "",
            "message_type": getattr(m, "message_type", "") or "",
            "content": getattr(m, "content", "") or "",
            "created_at": (
                getattr(m, "inserted_at", None).isoformat()
                if getattr(m, "inserted_at", None) is not None
                else ""
            ),
            "updated_at": (
                getattr(m, "updated_at", None).isoformat()
                if getattr(m, "updated_at", None) is not None
                else ""
            ),
        }

    def list_room_messages(
        self, room_id: str, limit_per_agent: int = 50
    ) -> List[dict]:
        """Fetch the real room transcript via the Context API.

        The Agent API context endpoint returns the real message history the
        agent has in the room (text messages plus platform tool_call /
        tool_result / system events). Each agent's view is merged and
        deduplicated by message ID so the caller receives the full transcript
        with the correct ``message_type`` — letting the backend and frontend
        distinguish tool-result events from actual agent text responses.
        """
        seen: Dict[str, dict] = {}
        for key, client in self._clients.items():
            try:
                ctx = client.agent_api_context.get_agent_chat_context(
                    room_id,
                    request_options=DEFAULT_REQUEST_OPTIONS,
                )
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "Could not fetch BAND context for %s in room %s: %s",
                    self._agent_states[key]["name"],
                    room_id,
                    self._friendly_error(exc),
                )
                continue
            items = getattr(ctx, "data", None) or []
            for m in items:
                msg = self._transcript_from_message(m)
                if msg["id"] and msg["id"] not in seen:
                    seen[msg["id"]] = msg

        messages = sorted(seen.values(), key=lambda m: m["created_at"] or "")
        return messages

    def room_participants(self, room_id: str) -> List[dict]:
        """List real chat room participants (owner's client, real API)."""
        owner_key = next((k for k in _SENDER_ORDER if k in self._clients), None)
        if not owner_key:
            return []
        try:
            response = self._clients[owner_key].agent_api_participants.list_agent_chat_participants(
                room_id,
                request_options=DEFAULT_REQUEST_OPTIONS,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Could not list participants for BAND room %s: %s",
                room_id,
                self._friendly_error(exc),
            )
            return []
        items = getattr(response, "data", None) or getattr(response, "items", None) or []
        if hasattr(items, "items"):
            items = items.items
        participants = []
        for p in items:
            participants.append(
                {
                    "id": getattr(p, "id", "") or "",
                    "name": getattr(p, "name", None),
                    "handle": getattr(p, "handle", "") or "",
                    "type": getattr(p, "type", "") or "",
                    "role": getattr(p, "role", "") or "",
                }
            )
        return participants


    def send_message(
        self,
        agent_name: str,
        message: str,
        task: str = "",
        handoff_to: Optional[str] = None,
    ) -> dict:
        """Send a real Band chat message to one of the registered agents.

        The message is sent by another authenticated agent into a shared Band
        chat, mentioning the target agent. No output is fabricated.
        """
        self._require_available()

        target = self._resolve_agent(agent_name)
        if target is None:
            raise RuntimeError(f"Unknown BAND agent '{agent_name}'.")
        if not target["authenticated"]:
            raise RuntimeError(
                f"BAND agent '{target['name']}' is not authenticated: {target['error']}"
            )

        # Create the shared chat first so sender selection only considers
        # agents that actually joined it.
        self._ensure_room()
        sender_key = self._sender_for(target["key"])
        if sender_key is None:
            raise RuntimeError("No second authenticated BAND agent is available.")

        content = message
        if task:
            content = f"Task: {task}\n\n{message}"

        extra_mentions: List[str] = []
        handoff = self._resolve_agent(handoff_to) if handoff_to else None
        if handoff and handoff["authenticated"] and handoff["key"] != target["key"]:
            extra_mentions.append(handoff["key"])

        result = self._send_to_agent(
            sender_key=sender_key,
            target_key=target["key"],
            content=content,
            extra_mentions=extra_mentions,
        )

        sender = self._agent_states[sender_key]
        return {
            "ok": True,
            "agent_name": target["name"],
            "agent_role": target["role"],
            "task": task,
            "status": "sent",
            "message": content,
            "output": "",
            "handoff_to": handoff["key"] if handoff else "",
            "agent_id": target["remote_id"],
            "sender": sender["name"],
            "sender_id": sender["remote_id"],
            "chat_id": result["chat_id"],
            "message_id": result["message_id"],
            "success": result["success"],
            "recipients": result["recipients"],
            "sent_at": _utcnow(),
            "room_warnings": self._room_warnings,
        }

    # ---------- CompeteIQ BAND AI workflow ----------

    def run_workflow(
        self,
        event: dict,
        historical_context: Optional[str] = None,
        reflection_text: Optional[str] = None,
        stored_room_id: Optional[str] = None,
        room_title: Optional[str] = None,
    ) -> List[dict]:
        """Dispatch the 7-agent workflow through real Band chats/messages.

        The backend finds or creates a Band chat (reusing ``stored_room_id``
        for the event to avoid duplicate rooms), adds the authenticated agents
        as participants, and sends each agent its task as a real message.
        ``historical_context`` is the real Hindsight recall context injected
        into the Historical Intelligence Agent's task, and ``reflection_text``
        is the real Hindsight reflect synthesis injected into the Strategy
        Agent's task. Agent replies are produced by the persistent workers in
        band_worker.py; this method never invents agent output.
        """
        self._require_available()

        title = event.get("title", "")
        company = event.get("company", "")
        description = event.get("description", "")
        category = event.get("category", "")

        # Fail early with a real error if a chat cannot be created.
        room_id = self._ensure_room(room_id=stored_room_id, title=room_title)

        agent_results: List[dict] = []
        previous: List[str] = []

        for idx, adef in enumerate(BAND_AGENT_DEFS):
            state = self._agent_states[adef["key"]]
            next_key = (
                BAND_AGENT_DEFS[idx + 1]["key"]
                if idx + 1 < len(BAND_AGENT_DEFS)
                else ""
            )

            message_content = (
                f"Event: {title} ({company}, {category})\n"
                f"Description: {description}\n"
                f"Your role: {adef['role']}\n"
                f"Task: {adef['task']}\n"
            )
            if adef["key"] == "historical" and historical_context:
                message_content += (
                    "\nRelevant historical memories retrieved from the CompeteIQ "
                    "Hindsight bank (real recall results; use and cite them):\n"
                    f"{historical_context}\n"
                )
            if adef["key"] == "strategy" and reflection_text:
                message_content += (
                    "\nHindsight reflect synthesis of historical experiences "
                    "(real reflect result; incorporate it):\n"
                    f"{reflection_text[:2000]}\n"
                )
            if previous:
                message_content += "\nPrevious agent messages:\n" + "\n".join(previous[-3:])

            base_result = {
                "step": idx + 1,
                "agent_name": adef["name"],
                "agent_role": adef["role"],
                "task": adef["task"],
                "message": message_content,
                "output": "",
                "handoff_to": next_key,
                "agent_id": state["remote_id"],
                "chat_id": room_id,
            }

            if not state["configured"]:
                base_result.update(status="not_configured", error=state["error"])
                agent_results.append(base_result)
                continue

            if not state["authenticated"]:
                base_result.update(status="failed", error=state["error"])
                agent_results.append(base_result)
                continue

            sender_key = self._sender_for(adef["key"])
            if sender_key is None:
                base_result.update(
                    status="failed",
                    error="No authenticated sender available.",
                )
                agent_results.append(base_result)
                continue

            if idx > 0:
                # Stagger dispatches between workflow steps to stay under
                # Band rate limits across rapid repeat runs.
                time.sleep(self.DISPATCH_STAGGER_SECONDS)

            try:
                sent = self._send_to_agent(
                    sender_key=sender_key,
                    target_key=adef["key"],
                    content=message_content,
                    extra_mentions=[next_key] if next_key else None,
                )
                base_result.update(
                    status="sent",
                    sender=self._agent_states[sender_key]["name"],
                    message_id=sent["message_id"],
                    success=sent["success"],
                    recipients=sent["recipients"],
                    dispatched_at=_utcnow(),
                )
                previous.append(f"- {adef['name']}: dispatched via {base_result['sender']}")
            except RuntimeError as exc:
                # One retry protects the chain against transient rate limits.
                time.sleep(self.DISPATCH_RETRY_DELAY_SECONDS)
                try:
                    sent = self._send_to_agent(
                        sender_key=sender_key,
                        target_key=adef["key"],
                        content=message_content,
                        extra_mentions=[next_key] if next_key else None,
                    )
                    base_result.update(
                        status="sent",
                        sender=self._agent_states[sender_key]["name"],
                        message_id=sent["message_id"],
                        success=sent["success"],
                        recipients=sent["recipients"],
                        dispatched_at=_utcnow(),
                    )
                    previous.append(f"- {adef['name']}: dispatched via {base_result['sender']}")
                except RuntimeError as retry_exc:
                    base_result.update(status="failed", error=str(retry_exc))

            agent_results.append(base_result)

        return agent_results


# Singleton instance
band_integration = BandIntegration()
