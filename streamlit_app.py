#!/usr/bin/env python3
"""
AI Travel Concierge — Streamlit Dashboard
Professional web interface for the agentic travel planning workflow.

Run with:
    streamlit run streamlit_app.py
"""

import os
import sys
import json
import time
import asyncio

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st

# ---------------------------------------------------------------------------
# Page configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="AI Travel Concierge",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Design tokens and CSS
# ---------------------------------------------------------------------------
CUSTOM_CSS = """
<style>
    /* ---------- Global ---------- */
    .block-container { padding-top: 1.8rem; }

    /* ---------- Header ---------- */
    .app-header {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        padding: 1.8rem 2.4rem;
        border-radius: 8px;
        color: #ffffff;
        margin-bottom: 1.6rem;
        border-bottom: 3px solid #0078d4;
    }
    .app-header h1 {
        margin: 0;
        font-size: 1.75rem;
        font-weight: 700;
        letter-spacing: -0.4px;
    }
    .app-header .subtitle {
        margin: 0.4rem 0 0 0;
        font-size: 0.85rem;
        opacity: 0.72;
        font-weight: 400;
    }

    /* ---------- Workflow Pipeline ---------- */
    .workflow-container {
        display: flex;
        align-items: flex-start;
        justify-content: center;
        padding: 1.4rem 0.8rem 1rem 0.8rem;
        background: #f8f9fb;
        border-radius: 8px;
        border: 1px solid #e2e6ea;
        margin-bottom: 1.2rem;
        overflow-x: auto;
    }
    .workflow-step {
        display: flex;
        flex-direction: column;
        align-items: center;
        min-width: 82px;
    }
    .step-node {
        width: 34px;
        height: 34px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 0.78rem;
        font-weight: 700;
        border: 2px solid #cbd5e1;
        background: #ffffff;
        color: #94a3b8;
        transition: all 0.3s ease;
    }
    .step-label {
        margin-top: 0.35rem;
        font-size: 0.72rem;
        color: #94a3b8;
        font-weight: 500;
        text-align: center;
        white-space: nowrap;
    }
    .step-desc {
        font-size: 0.62rem;
        color: #b0b8c4;
        margin-top: 0.1rem;
        text-align: center;
        max-width: 80px;
    }
    .step-time {
        font-size: 0.62rem;
        color: #94a3b8;
        margin-top: 0.15rem;
        font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
    }
    .workflow-connector {
        width: 36px;
        height: 2px;
        background: #cbd5e1;
        margin: 16px 2px 0 2px;
        transition: background 0.3s ease;
    }

    /* Phase states */
    .step-completed .step-node {
        background: #0f3460;
        border-color: #0f3460;
        color: #ffffff;
    }
    .step-completed .step-label {
        color: #0f3460;
        font-weight: 600;
    }
    .step-completed .step-desc { color: #64748b; }
    .step-completed .step-time { color: #64748b; }

    .step-active .step-node {
        background: #0078d4;
        border-color: #0078d4;
        color: #ffffff;
        box-shadow: 0 0 0 4px rgba(0, 120, 212, 0.2);
        animation: pulse 1.5s infinite;
    }
    .step-active .step-label {
        color: #0078d4;
        font-weight: 600;
    }
    .step-active .step-desc { color: #0078d4; }

    .connector-done { background: #0f3460; }

    .step-error .step-node {
        background: #dc2626;
        border-color: #dc2626;
        color: #ffffff;
    }
    .step-error .step-label { color: #dc2626; font-weight: 600; }

    @keyframes pulse {
        0%, 100% { box-shadow: 0 0 0 4px rgba(0, 120, 212, 0.2); }
        50%       { box-shadow: 0 0 0 8px rgba(0, 120, 212, 0.08); }
    }

    /* ---------- Execution Log ---------- */
    .exec-log {
        font-family: 'SF Mono', 'Fira Code', 'Consolas', monospace;
        font-size: 0.76rem;
        line-height: 1.65;
        color: #334155;
        background: #f8f9fb;
        border: 1px solid #e2e6ea;
        border-radius: 6px;
        padding: 0.8rem 1rem;
        margin-bottom: 1.2rem;
        max-height: 220px;
        overflow-y: auto;
    }
    .log-ts   { color: #94a3b8; }
    .log-ph   { color: #0f3460; font-weight: 600; }
    .log-ok   { color: #059669; font-weight: 600; }
    .log-err  { color: #dc2626; font-weight: 600; }
    .log-det  { color: #64748b; }

    /* ---------- Result cards ---------- */
    .result-card {
        background: #ffffff;
        border: 1px solid #e2e6ea;
        border-left: 4px solid #0f3460;
        padding: 1.1rem 1.3rem;
        border-radius: 6px;
        margin-bottom: 0.7rem;
    }
    .result-card h4 {
        margin: 0 0 0.4rem 0;
        color: #1a1a2e;
        font-size: 0.95rem;
    }
    .result-card p {
        margin: 0.15rem 0;
        color: #475569;
        font-size: 0.88rem;
    }

    /* ---------- Sidebar ---------- */
    .sidebar-box {
        background: #f8f9fb;
        padding: 0.9rem 1rem;
        border-radius: 6px;
        border: 1px solid #e2e6ea;
        margin-bottom: 0.8rem;
    }
    .sidebar-box h4 {
        margin: 0 0 0.4rem 0;
        color: #1a1a2e;
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .sidebar-box p {
        margin: 0;
        font-size: 0.8rem;
        color: #475569;
        line-height: 1.5;
    }

    /* ---------- Metric card override ---------- */
    [data-testid="stMetric"] {
        background: #f8f9fb;
        border: 1px solid #e2e6ea;
        padding: 0.7rem 0.9rem;
        border-radius: 6px;
    }
    [data-testid="stMetricLabel"] { font-size: 0.78rem !important; }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Phase definitions
# ---------------------------------------------------------------------------
PHASES = [
    {"id": 1, "key": "Init",                    "label": "Init",     "desc": "Initialize session"},
    {"id": 2, "key": "ClarifyRequirements",      "label": "Clarify",  "desc": "Extract requirements"},
    {"id": 3, "key": "PlanTools",                 "label": "Plan",     "desc": "Configure kernel"},
    {"id": 4, "key": "ExecuteTools",              "label": "Execute",  "desc": "Run tool plugins"},
    {"id": 5, "key": "AnalyzeResults",            "label": "Analyze",  "desc": "Validate data"},
    {"id": 6, "key": "ResolveIssues",             "label": "Resolve",  "desc": "Handle issues"},
    {"id": 7, "key": "ProduceStructuredOutput",   "label": "Produce",  "desc": "Build JSON output"},
    {"id": 8, "key": "Done",                      "label": "Done",     "desc": "Complete"},
]


def build_workflow_html(
    current_phase: int = 0,
    phase_times: dict | None = None,
    error_phase: int | None = None,
) -> str:
    """Render the horizontal workflow stepper as HTML."""
    phase_times = phase_times or {}
    parts = ['<div class="workflow-container">']

    for i, ph in enumerate(PHASES):
        pid = ph["id"]

        # Determine visual state
        if error_phase and pid == error_phase:
            cls = "step-error"
        elif pid < current_phase:
            cls = "step-completed"
        elif pid == current_phase:
            cls = "step-active"
        else:
            cls = ""

        # Checkmark for completed, number otherwise
        icon = "&#10003;" if pid < current_phase else str(pid)

        # Timing label
        time_html = ""
        if pid in phase_times:
            ms = phase_times[pid]
            time_html = f'<div class="step-time">{ms:.0f} ms</div>'

        parts.append(
            f'<div class="workflow-step {cls}">'
            f'  <div class="step-node">{icon}</div>'
            f'  <div class="step-label">{ph["label"]}</div>'
            f'  <div class="step-desc">{ph["desc"]}</div>'
            f'  {time_html}'
            f'</div>'
        )

        # Connector line between nodes
        if i < len(PHASES) - 1:
            conn_cls = "connector-done" if pid < current_phase else ""
            parts.append(f'<div class="workflow-connector {conn_cls}"></div>')

    parts.append("</div>")
    return "".join(parts)


def build_log_html(entries: list) -> str:
    """Render the phase execution log as monospace HTML."""
    if not entries:
        return ""
    lines = []
    for e in entries:
        status_cls = "log-err" if e.get("error") else "log-ok"
        status_txt = "ERR" if e.get("error") else "OK"
        detail = f' <span class="log-det">{e["detail"]}</span>' if e.get("detail") else ""
        lines.append(
            f'<span class="log-ts">[{e["ts"]}]</span> '
            f'<span class="log-ph">Phase {e["phase"]}/{len(PHASES)}</span> '
            f'{e["label"]} '
            f'<span class="{status_cls}">[{status_txt}]</span>'
            f'{detail}'
        )
    return f'<div class="exec-log">{"<br>".join(lines)}</div>'


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown(
    '<div class="app-header">'
    "  <h1>AI Travel Concierge</h1>"
    '  <div class="subtitle">'
    "Semantic Kernel  |  Azure OpenAI (gpt-4o-mini)  |  Cosmos DB RAG  |  Bing Grounding"
    "  </div>"
    "</div>",
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("### Trip Configuration")

    destinations = [
        "Paris", "Tokyo", "London", "Barcelona", "Rome",
        "Berlin", "Sydney", "Dubai", "Singapore", "New York",
    ]
    destination = st.selectbox("Destination", destinations, index=0)

    col_s, col_e = st.columns(2)
    with col_s:
        start_date = st.date_input("Start")
    with col_e:
        end_date = st.date_input("End")

    card = st.selectbox(
        "Credit Card",
        ["BankGold", "BankPlatinum", "BankRewards"],
        index=0,
    )

    use_sidebar = st.checkbox("Prepend sidebar settings to query", value=True)

    st.divider()

    st.markdown("### System")

    st.markdown(
        '<div class="sidebar-box">'
        "<h4>Architecture</h4>"
        "<p>8-phase state machine with 5 tool plugins, "
        "RAG knowledge base via Cosmos DB, "
        "Bing Grounding search via AI Foundry Agent.</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="sidebar-box">'
        "<h4>Tool Plugins</h4>"
        "<p>WeatherTools &middot; FxTools &middot; SearchTools "
        "&middot; CardTools &middot; KnowledgeTools</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="sidebar-box">'
        "<h4>Models</h4>"
        "<p>Chat: gpt-4o-mini<br>"
        "Embeddings: text-embedding-3-small<br>"
        "Agent: gpt-4o (Bing grounding)</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    st.caption("Udacity AI Foundry  |  Project 3")

# ---------------------------------------------------------------------------
# Session state
# ---------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "wf_phase" not in st.session_state:
    st.session_state.wf_phase = 0
if "wf_times" not in st.session_state:
    st.session_state.wf_times = {}
if "wf_logs" not in st.session_state:
    st.session_state.wf_logs = []
if "wf_error" not in st.session_state:
    st.session_state.wf_error = None

# ---------------------------------------------------------------------------
# Workflow visualization (persistent placeholder)
# ---------------------------------------------------------------------------
wf_placeholder = st.empty()
wf_placeholder.markdown(
    build_workflow_html(
        st.session_state.wf_phase,
        st.session_state.wf_times,
        st.session_state.wf_error,
    ),
    unsafe_allow_html=True,
)

log_placeholder = st.empty()
if st.session_state.wf_logs:
    log_placeholder.markdown(
        build_log_html(st.session_state.wf_logs),
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Chat history
# ---------------------------------------------------------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ---------------------------------------------------------------------------
# Chat input
# ---------------------------------------------------------------------------
user_input = st.chat_input(
    "Describe your travel plans (e.g. 'Plan a trip to Paris, June 1-8, BankGold card')"
)

if user_input:
    # Build prompt
    if use_sidebar:
        prompt = (
            f"I want to travel to {destination} "
            f"from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')} "
            f"with my {card} card. {user_input}"
        )
    else:
        prompt = user_input

    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Reset workflow tracking
    st.session_state.wf_phase = 0
    st.session_state.wf_times = {}
    st.session_state.wf_logs = []
    st.session_state.wf_error = None

    # ------------------------------------------------------------------
    # Agent Execution — step-by-step with live workflow updates
    # ------------------------------------------------------------------
    with st.chat_message("assistant"):
        from app.main import (
            extract_requirements_from_input,
            create_kernel,
            execute_tools,
        )
        from app.synthesis import synthesize_to_tripplan
        from app.state import AgentState, Phase

        state = AgentState()
        logs: list[dict] = []
        phase_times: dict[int, float] = {}
        error_phase: int | None = None

        def _update(phase_num: int, label: str):
            """Set a phase as active in the pipeline."""
            st.session_state.wf_phase = phase_num
            wf_placeholder.markdown(
                build_workflow_html(phase_num, phase_times, error_phase),
                unsafe_allow_html=True,
            )

        def _complete(phase_num: int, label: str, elapsed_ms: float, detail: str = ""):
            """Mark phase completed, record timing, append log entry."""
            phase_times[phase_num] = elapsed_ms
            st.session_state.wf_times = phase_times
            logs.append({
                "ts": time.strftime("%H:%M:%S"),
                "phase": phase_num,
                "label": label,
                "detail": f"{elapsed_ms:.0f} ms" + (f"  {detail}" if detail else ""),
            })
            st.session_state.wf_logs = logs
            wf_placeholder.markdown(
                build_workflow_html(phase_num + 1, phase_times, error_phase),
                unsafe_allow_html=True,
            )
            log_placeholder.markdown(build_log_html(logs), unsafe_allow_html=True)

        try:
            # ---- Phase 1: Init ----
            t0 = time.time()
            _update(1, "Initializing")
            state.phase = Phase.Init
            elapsed = (time.time() - t0) * 1000
            _complete(1, "Session initialized", elapsed, f"sid:{state.session_id[:8]}")

            # ---- Phase 2: Clarify Requirements ----
            t0 = time.time()
            _update(2, "Extracting requirements")
            requirements = extract_requirements_from_input(prompt)
            state.set_requirements(requirements)
            if not requirements.get("destination"):
                requirements["destination"] = destination
            elapsed = (time.time() - t0) * 1000
            _complete(
                2, "Requirements extracted", elapsed,
                f"{requirements.get('destination', '?')} / {requirements.get('card', '?')}",
            )

            # ---- Phase 3: Plan Tools ----
            t0 = time.time()
            _update(3, "Creating Semantic Kernel")
            kernel = create_kernel()
            elapsed = (time.time() - t0) * 1000
            _complete(3, "Kernel configured", elapsed, "5 plugins registered")

            # ---- Phase 4: Execute Tools ----
            t0 = time.time()
            _update(4, "Executing tool plugins")
            loop = asyncio.new_event_loop()
            tool_results = loop.run_until_complete(
                execute_tools(kernel, state, requirements)
            )
            loop.close()
            tools_ok = len(state.tools_called) - len(state.tool_errors)
            elapsed = (time.time() - t0) * 1000
            _complete(
                4, "Tools executed", elapsed,
                f"{tools_ok}/{len(state.tools_called)} succeeded",
            )

            # ---- Phase 5: Analyze Results ----
            t0 = time.time()
            _update(5, "Validating data")
            analysis = {
                "tools_executed": len(state.tools_called),
                "tools_with_errors": len(state.tool_errors),
                "data_quality": "good" if len(state.tool_errors) < 2 else "partial",
            }
            state.set_analysis_results(analysis)
            elapsed = (time.time() - t0) * 1000
            _complete(
                5, "Analysis complete", elapsed,
                f"quality: {analysis['data_quality']}",
            )

            # ---- Phase 6: Resolve Issues ----
            t0 = time.time()
            _update(6, "Resolving issues")
            issue_count = 0
            if state.tool_errors:
                for tool, err in state.tool_errors.items():
                    state.add_issue(f"Tool {tool} failed: {err}")
                    state.add_resolution_attempt(f"Fallback for {tool}")
                    state.resolve_issue(f"Tool {tool} failed: {err}")
                    issue_count += 1
            elapsed = (time.time() - t0) * 1000
            _complete(
                6, "Issues resolved", elapsed,
                f"{issue_count} issue(s) handled" if issue_count else "none",
            )

            # ---- Phase 7: Produce Structured Output ----
            t0 = time.time()
            _update(7, "Building structured output")
            result_json = synthesize_to_tripplan(tool_results, requirements)
            plan_data = json.loads(result_json)
            elapsed = (time.time() - t0) * 1000
            _complete(7, "TripPlan produced", elapsed, "Pydantic-validated JSON")

            # ---- Phase 8: Done ----
            phase_times[8] = 0
            st.session_state.wf_times = phase_times
            logs.append({
                "ts": time.strftime("%H:%M:%S"),
                "phase": 8,
                "label": "Workflow complete",
                "detail": f"total: {sum(phase_times.values()):.0f} ms",
            })
            st.session_state.wf_logs = logs
            st.session_state.wf_phase = 9  # all done
            wf_placeholder.markdown(
                build_workflow_html(9, phase_times),
                unsafe_allow_html=True,
            )
            log_placeholder.markdown(build_log_html(logs), unsafe_allow_html=True)

            # ----------------------------------------------------------
            # Render results
            # ----------------------------------------------------------
            if "error" in plan_data:
                st.error(plan_data["error"])
            else:
                plan = plan_data.get("plan", {})

                st.markdown("---")
                st.markdown(f"### {plan.get('destination', destination)}")
                st.caption(f"Travel dates: {plan.get('travel_dates', 'N/A')}")

                # Metric cards
                weather = plan.get("weather") or {}
                currency = plan.get("currency_info") or {}
                card_rec = plan.get("card_recommendation") or {}

                m1, m2, m3, m4 = st.columns(4)
                m1.metric(
                    "Temperature",
                    f"{weather.get('temperature_c', '--')} C"
                    if weather.get("temperature_c") is not None
                    else "N/A",
                )
                m2.metric(
                    "Exchange Rate",
                    str(currency.get("usd_to_eur", "N/A")),
                    "USD base",
                )
                m3.metric("Recommended Card", card_rec.get("card", "N/A"))
                m4.metric("FX Fee", card_rec.get("fx_fee", "N/A"))

                # Detail tabs
                (
                    tab_weather,
                    tab_search,
                    tab_card,
                    tab_currency,
                    tab_steps,
                    tab_json,
                ) = st.tabs(
                    [
                        "Weather",
                        "Search Results",
                        "Card",
                        "Currency",
                        "Next Steps",
                        "Raw JSON",
                    ]
                )

                with tab_weather:
                    if weather:
                        st.markdown(
                            '<div class="result-card">'
                            "<h4>Weather Forecast</h4>"
                            f'<p><strong>Conditions:</strong> {weather.get("conditions", "N/A")}</p>'
                            f'<p><strong>Temperature:</strong> {weather.get("temperature_c", "N/A")} C</p>'
                            f'<p><strong>Recommendation:</strong> {weather.get("recommendation", "N/A")}</p>'
                            "</div>",
                            unsafe_allow_html=True,
                        )
                    else:
                        st.info("No weather data available.")

                with tab_search:
                    results = plan.get("results") or []
                    if results:
                        for idx, r in enumerate(results, 1):
                            rating = (
                                f" | Rating: {r['rating']}/5" if r.get("rating") else ""
                            )
                            price = (
                                f" | Price: {r['price_range']}"
                                if r.get("price_range")
                                else ""
                            )
                            url_html = (
                                f'<p><a href="{r["url"]}" target="_blank">{r["url"]}</a></p>'
                                if r.get("url")
                                else ""
                            )
                            st.markdown(
                                '<div class="result-card">'
                                f'<h4>{idx}. {r.get("title", "Untitled")}</h4>'
                                f'<p>{r.get("snippet", "")}{rating}{price}</p>'
                                f"{url_html}"
                                "</div>",
                                unsafe_allow_html=True,
                            )
                    else:
                        st.info("No search results available.")

                with tab_card:
                    if card_rec:
                        st.markdown(
                            '<div class="result-card">'
                            f'<h4>{card_rec.get("card", "N/A")}</h4>'
                            f'<p><strong>Benefit:</strong> {card_rec.get("benefit", "N/A")}</p>'
                            f'<p><strong>FX Fee:</strong> {card_rec.get("fx_fee", "N/A")}</p>'
                            f'<p><strong>Source:</strong> {card_rec.get("source", "N/A")}</p>'
                            "</div>",
                            unsafe_allow_html=True,
                        )
                    else:
                        st.info("No card recommendation available.")

                with tab_currency:
                    if currency:
                        c1, c2 = st.columns(2)
                        c1.metric(
                            "Sample Meal (USD)",
                            f"${currency.get('sample_meal_usd', '--')}",
                        )
                        c2.metric(
                            "Sample Meal (local)",
                            str(currency.get("sample_meal_eur", "--")),
                        )
                        if currency.get("points_earned"):
                            st.metric("Points Earned", currency["points_earned"])
                    else:
                        st.info("No currency data available.")

                with tab_steps:
                    steps = plan.get("next_steps", [])
                    if steps:
                        for idx, step in enumerate(steps, 1):
                            st.markdown(f"**{idx}.** {step}")
                    else:
                        st.info("No next steps available.")

                with tab_json:
                    st.json(plan_data)

                # Citations
                citations = plan.get("citations") or []
                if citations:
                    with st.expander("Sources and Citations"):
                        for c in citations:
                            st.markdown(f"- {c}")

                # Store summary in chat history
                summary = (
                    f"Trip plan for **{plan.get('destination', destination)}** "
                    f"({plan.get('travel_dates', 'N/A')}).\n\n"
                    f"- Weather: {weather.get('conditions', 'N/A')} | "
                    f"{weather.get('temperature_c', '--')} C\n"
                    f"- Card: {card_rec.get('card', 'N/A')} -- "
                    f"{card_rec.get('benefit', '')}\n"
                    f"- FX Fee: {card_rec.get('fx_fee', 'N/A')}\n\n"
                    f"See the detail tabs for the full plan."
                )
                st.session_state.messages.append(
                    {"role": "assistant", "content": summary}
                )

        except Exception as exc:
            # Record the error in the workflow visualization
            error_phase = st.session_state.wf_phase or 1
            st.session_state.wf_error = error_phase
            logs.append({
                "ts": time.strftime("%H:%M:%S"),
                "phase": error_phase,
                "label": "Error",
                "detail": str(exc),
                "error": True,
            })
            st.session_state.wf_logs = logs
            wf_placeholder.markdown(
                build_workflow_html(error_phase, phase_times, error_phase),
                unsafe_allow_html=True,
            )
            log_placeholder.markdown(build_log_html(logs), unsafe_allow_html=True)

            st.error(f"Agent error: {exc}")
            import traceback

            st.code(traceback.format_exc())
            st.session_state.messages.append(
                {"role": "assistant", "content": f"An error occurred: {exc}"}
            )
