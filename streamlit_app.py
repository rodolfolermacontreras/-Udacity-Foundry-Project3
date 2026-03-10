#!/usr/bin/env python3
"""
Streamlit UI for the AI Travel Concierge Agent.

Run with:
    streamlit run streamlit_app.py
"""

import os
import sys
import json
import asyncio

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import streamlit as st

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="AI Travel Concierge",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    /* Header banner */
    .main-header {
        background: linear-gradient(135deg, #0078D4 0%, #005A9E 100%);
        padding: 1.5rem 2rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 1.5rem;
    }
    .main-header h1 { margin: 0; font-size: 2rem; }
    .main-header p  { margin: 0.3rem 0 0 0; opacity: 0.9; }

    /* Result cards */
    .result-card {
        background: #f8f9fa;
        border-left: 4px solid #0078D4;
        padding: 1rem 1.2rem;
        border-radius: 6px;
        margin-bottom: 0.8rem;
    }
    .result-card h4 { margin: 0 0 0.4rem 0; color: #0078D4; }

    /* Phase badge */
    .phase-badge {
        display: inline-block;
        background: #e6f2ff;
        color: #0078D4;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 0.82rem;
        font-weight: 600;
        margin-right: 6px;
        margin-bottom: 4px;
    }
    .phase-badge.done {
        background: #e6f9ed;
        color: #0a7c3e;
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
st.markdown("""
<div class="main-header">
    <h1>✈️ AI Travel Concierge</h1>
    <p>Powered by Microsoft Semantic Kernel &bull; Azure OpenAI &bull; Cosmos DB RAG</p>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Sidebar – configuration & quick picks
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("Trip Settings")

    destinations = [
        "Paris", "Tokyo", "London", "Barcelona", "Rome",
        "Berlin", "Sydney", "Dubai", "Singapore", "New York",
    ]
    destination = st.selectbox("Destination", destinations, index=0)

    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start date")
    with col2:
        end_date = st.date_input("End date")

    card = st.selectbox(
        "Credit Card",
        ["BankGold", "BankPlatinum", "BankRewards"],
        index=0,
    )

    use_quick = st.checkbox("Use quick-pick settings above", value=True)

    st.divider()
    st.subheader("Architecture")
    st.markdown(
        "8-phase state machine with 5 tool plugins, "
        "RAG via Cosmos DB, and Bing Grounding search."
    )

    phases = [
        "1 · Init", "2 · Clarify", "3 · PlanTools",
        "4 · Execute", "5 · Analyze", "6 · Resolve",
        "7 · Produce", "8 · Done",
    ]
    st.caption("Agent Workflow Phases")
    for p in phases:
        st.markdown(f'<span class="phase-badge">{p}</span>', unsafe_allow_html=True)

    st.divider()
    st.caption("Built for Udacity AI Foundry Project 3")

# ---------------------------------------------------------------------------
# Chat area
# ---------------------------------------------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "plan_history" not in st.session_state:
    st.session_state.plan_history = []

# Render chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"], avatar="✈️" if msg["role"] == "assistant" else None):
        st.markdown(msg["content"])

# Chat input
user_input = st.chat_input("Where would you like to travel? (e.g. 'Plan a trip to Paris June 1-8 with BankGold')")

if user_input:
    # Build the prompt – optionally inject sidebar settings
    if use_quick:
        prompt = (
            f"I want to travel to {destination} "
            f"from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')} "
            f"with my {card} card. {user_input}"
        )
    else:
        prompt = user_input

    # Show user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Process via agent
    with st.chat_message("assistant", avatar="✈️"):
        status = st.status("Processing your trip request...", expanded=True)

        phase_names = [
            "Init", "ClarifyRequirements", "PlanTools",
            "ExecuteTools", "AnalyzeResults", "ResolveIssues",
            "ProduceStructuredOutput", "Done",
        ]

        # Show phase progression
        for i, phase in enumerate(phase_names[:-1], 1):
            status.update(label=f"Phase {i}/8 – {phase}")

        try:
            from app.main import run_request

            # Run the async agent
            loop = asyncio.new_event_loop()
            result_json = loop.run_until_complete(run_request(prompt))
            loop.close()

            plan_data = json.loads(result_json)

            if "error" in plan_data:
                status.update(label="Error", state="error")
                st.error(plan_data["error"])
            else:
                status.update(label="Phase 8/8 – Done", state="complete")
                plan = plan_data.get("plan", {})

                # Store in history
                st.session_state.plan_history.append(plan)

                # ---- Render the trip plan ----
                st.subheader(f"Trip to {plan.get('destination', destination)}")
                st.caption(f"Dates: {plan.get('travel_dates', 'N/A')}")

                # Metric row
                weather = plan.get("weather") or {}
                currency = plan.get("currency_info") or {}
                card_rec = plan.get("card_recommendation") or {}

                m1, m2, m3, m4 = st.columns(4)
                m1.metric(
                    "Temperature",
                    f"{weather.get('temperature_c', '--')} °C" if weather.get("temperature_c") is not None else "N/A",
                )
                m2.metric(
                    "Exchange Rate",
                    f"{currency.get('usd_to_eur', '--')}" if currency.get("usd_to_eur") else "N/A",
                    "USD base",
                )
                m3.metric("Recommended Card", card_rec.get("card", "N/A"))
                m4.metric("FX Fee", card_rec.get("fx_fee", "N/A"))

                # Tabs for details
                tab_weather, tab_search, tab_card, tab_currency, tab_steps, tab_json = st.tabs(
                    ["Weather", "Search Results", "Card", "Currency", "Next Steps", "Raw JSON"]
                )

                with tab_weather:
                    if weather:
                        st.markdown(f'<div class="result-card"><h4>Weather Forecast</h4>'
                                    f'<b>Conditions:</b> {weather.get("conditions", "N/A")}<br>'
                                    f'<b>Recommendation:</b> {weather.get("recommendation", "N/A")}'
                                    f'</div>', unsafe_allow_html=True)
                    else:
                        st.info("No weather data available.")

                with tab_search:
                    results = plan.get("results") or []
                    if results:
                        for i, r in enumerate(results, 1):
                            with st.container():
                                st.markdown(
                                    f'<div class="result-card">'
                                    f'<h4>{i}. {r.get("title", "Untitled")}</h4>'
                                    f'{r.get("snippet", "") or ""}'
                                    + (f'<br><b>Rating:</b> {r["rating"]}/5' if r.get("rating") else "")
                                    + (f' &middot; <b>Price:</b> {r["price_range"]}' if r.get("price_range") else "")
                                    + (f'<br><a href="{r["url"]}" target="_blank">{r["url"]}</a>' if r.get("url") else "")
                                    + '</div>',
                                    unsafe_allow_html=True,
                                )
                    else:
                        st.info("No search results available.")

                with tab_card:
                    if card_rec:
                        st.markdown(
                            f'<div class="result-card"><h4>{card_rec.get("card", "N/A")}</h4>'
                            f'<b>Benefit:</b> {card_rec.get("benefit", "N/A")}<br>'
                            f'<b>FX Fee:</b> {card_rec.get("fx_fee", "N/A")}<br>'
                            f'<b>Source:</b> {card_rec.get("source", "N/A")}'
                            f'</div>', unsafe_allow_html=True,
                        )
                    else:
                        st.info("No card recommendation available.")

                with tab_currency:
                    if currency:
                        c1, c2 = st.columns(2)
                        c1.metric("Sample Meal (USD)", f"${currency.get('sample_meal_usd', '--')}")
                        c2.metric("Sample Meal (local)", f"{currency.get('sample_meal_eur', '--')}")
                        if currency.get("points_earned"):
                            st.metric("Points Earned", currency["points_earned"])
                    else:
                        st.info("No currency data available.")

                with tab_steps:
                    for i, step in enumerate(plan.get("next_steps", []), 1):
                        st.markdown(f"**{i}.** {step}")

                with tab_json:
                    st.json(plan_data)

                # Citations
                citations = plan.get("citations") or []
                if citations:
                    with st.expander("Sources & Citations"):
                        for c in citations:
                            st.markdown(f"- {c}")

                # Build summary for chat history
                summary = (
                    f"Here is your trip plan for **{plan.get('destination', destination)}** "
                    f"({plan.get('travel_dates', 'N/A')}).\n\n"
                    f"- **Weather**: {weather.get('conditions', 'N/A')} · {weather.get('temperature_c', '--')} °C\n"
                    f"- **Card**: {card_rec.get('card', 'N/A')} – {card_rec.get('benefit', '')}\n"
                    f"- **FX Fee**: {card_rec.get('fx_fee', 'N/A')}\n\n"
                    f"See the tabs above for full details."
                )
                st.session_state.messages.append({"role": "assistant", "content": summary})

        except Exception as e:
            status.update(label="Error", state="error")
            st.error(f"Agent error: {e}")
            import traceback
            st.code(traceback.format_exc())
            st.session_state.messages.append(
                {"role": "assistant", "content": f"Sorry, I encountered an error: {e}"}
            )
