
import { useState, useEffect, useRef } from "react";
import {
  Swords,
  Check,
  Trophy,
  RotateCcw,
  Play,
  ShieldCheck,
  Brain
} from "lucide-react";

import "./CompetitorBattlePage.css";

const HEADINGS = [
  "Company Overview",
  "Products & Services",
  "AI Models & Technology",
  "Pricing Strategy",
  "Business Strategy",
  "Market Positioning",
  "Strengths & Weaknesses",
  "SWOT Analysis",
  "Hindsight Memory Insights",
  "Final Strategic Verdict"
];

const STEP_MS = 1400;
const TRANSITION_MS = 2200;

export default function CompetitorBattlePage() {
  const [phase, setPhase] = useState("intro");
  const [completed, setCompleted] = useState(0);
  const [shownPercent, setShownPercent] = useState(0);

  const startedRef = useRef(false);

  const total = HEADINGS.length;
  const targetPercent = Math.round((completed / total) * 100);

  // Run comparison headings one by one
  useEffect(() => {
    if (phase !== "running") return;

    if (completed >= total) {
      setPhase("clash");
      return;
    }

    const timer = setTimeout(() => {
      setCompleted((current) => current + 1);
    }, STEP_MS);

    return () => clearTimeout(timer);
  }, [phase, completed, total]);

  // Show final battle transition
  useEffect(() => {
    if (phase !== "clash") return;

    const timer = setTimeout(() => {
      setPhase("result");
    }, TRANSITION_MS);

    return () => clearTimeout(timer);
  }, [phase]);

  // Animate progress percentage
  useEffect(() => {
    if (shownPercent === targetPercent) return;

    const timer = setTimeout(() => {
      setShownPercent((current) =>
        current < targetPercent ? current + 1 : current - 1
      );
    }, 30);

    return () => clearTimeout(timer);
  }, [shownPercent, targetPercent]);

  // Start comparison
  const start = () => {
    if (startedRef.current) return;

    startedRef.current = true;
    setCompleted(0);
    setShownPercent(0);
    setPhase("running");
  };

  // Restart comparison
  const reset = () => {
    startedRef.current = false;
    setCompleted(0);
    setShownPercent(0);
    setPhase("intro");
  };

  return (
    <div className="cbp">

      <header className="cbp-head">
        <h1>Competitor Battle</h1>
        <p>
          CompeteIQ presentation mode. Simulated competitor,
          illustrative demo only.
        </p>
      </header>

      {(phase === "intro" || phase === "running") && (
        <section
          className={`cbp-arena ${
            phase === "running" ? "is-running" : ""
          }`}
        >

          <div className="cbp-fighters">

            <FighterCard
              side="left"
              name="NEXORA AI"
              tag="OUR COMPANY"
              line="AI-Powered Competitive Intelligence Platform"
            />

            <div className="cbp-vs">
              <span className="cbp-vs-ring" />
              <span className="cbp-vs-text">VS</span>
            </div>

            <FighterCard
              side="right"
              name="MINTY-GPT"
              tag="SIMULATED COMPETITOR"
              line="Demonstration competitor"
            />

          </div>

          {phase === "intro" && (
            <div className="cbp-cta">
              <button
                type="button"
                className="cbp-btn"
                onClick={start}
              >
                <Play size={18} />
                START COMPARISON
              </button>
            </div>
          )}

          {phase === "running" && (
            <div className="cbp-panel" aria-live="polite">

              <div className="cbp-progress-top">
                <span>Running demo comparison</span>
                <strong>{shownPercent}%</strong>
              </div>

              <div
                className="cbp-bar"
                role="progressbar"
                aria-valuemin={0}
                aria-valuemax={100}
                aria-valuenow={targetPercent}
              >
                <div
                  className="cbp-bar-fill"
                  style={{ width: `${targetPercent}%` }}
                />

                <div className="cbp-bar-scan" />
              </div>

              <ul className="cbp-list">

                {HEADINGS.map((heading, index) => {
                  const state =
                    index < completed
                      ? "done"
                      : index === completed
                      ? "active"
                      : "wait";

                  return (
                    <li
                      key={heading}
                      className={`cbp-row is-${state}`}
                    >

                      <span className="cbp-icon">
                        {state === "done" && (
                          <Check size={16} strokeWidth={3} />
                        )}

                        {state === "active" && (
                          <span className="cbp-spinner" />
                        )}
                      </span>

                      <span className="cbp-row-name">
                        {heading}
                      </span>

                      <span className="cbp-row-status">
                        {state === "done"
                          ? "COMPLETED"
                          : state === "active"
                          ? "ANALYZING"
                          : "QUEUED"}
                      </span>

                      {state === "active" && (
                        <span
                          className="cbp-row-scan"
                          key={completed}
                        />
                      )}

                    </li>
                  );
                })}

              </ul>

              <p className="cbp-note">
                Presentation animation only. No real competitor
                data is retrieved or analyzed.
              </p>

            </div>
          )}

        </section>
      )}

      {phase === "clash" && (
        <section className="cbp-clash" aria-live="polite">

          <div className="cbp-clash-side left">
            NEXORA AI
          </div>

          <Swords
            className="cbp-clash-icon"
            size={64}
            strokeWidth={1.5}
          />

          <div className="cbp-clash-side right">
            MINTY-GPT
          </div>

          <p>Calculating final demo verdict...</p>

        </section>
      )}

      {phase === "result" && (
        <section className="cbp-result">

          <div className="cbp-trophy">
            <Trophy size={72} strokeWidth={1.4} />
          </div>

          <h2 className="cbp-wins">
            NEXORA AI WINS
          </h2>

          <div className="cbp-verdict">
            🏆 NEXORA AI IS BETTER
          </div>

          <p className="cbp-sub">
            CompeteIQ Competitive Battle — Demo Result
          </p>

          <ul className="cbp-summary">

            <li>
              <ShieldCheck size={18} />
              Company comparison completed
            </li>

            <li>
              <ShieldCheck size={18} />
              10 comparison categories displayed
            </li>

            <li>
              <Brain size={18} />
              Hindsight memory section included in the demo
            </li>

            <li>
              <Trophy size={18} />
              Final illustrative verdict: NEXORA AI
            </li>

          </ul>

          <p className="cbp-disclaimer">
            Illustrative demo verdict. Not a verified real-world
            competitive assessment. MINTY-GPT is a fictional
            competitor created for demonstration.
          </p>

          <button
            type="button"
            className="cbp-btn"
            onClick={reset}
          >
            <RotateCcw size={18} />
            RUN COMPARISON AGAIN
          </button>

        </section>
      )}

    </div>
  );
}

function FighterCard({ side, name, tag, line }) {
  return (
    <article className={`cbp-card ${side}`}>

      <span className="cbp-card-tag">
        {tag}
      </span>

      <h2>{name}</h2>

      <p>{line}</p>

    </article>
  );
}
