"""LangGraph graph definition with branching control flow.

This is a genuine graph with conditional edges — NOT a linear chain.
"""

from __future__ import annotations

from langgraph.graph import StateGraph, END

from app.graph.state import AdvisoryState
from app.graph.nodes import (
    classify_intent,
    resolve_location,
    fetch_weather,
    evaluate_sops,
    resolve_conflicts_node,
    compose_response,
    location_failure,
    weather_failure,
    no_sop_fallback,
)


def _route_after_location(state: AdvisoryState) -> str:
    """Branch after location resolution."""
    error = state.get("error")
    if error in ("LOCATION_RESOLUTION_FAILED", "LOCATION_MISSING"):
        return "location_failure"
    return "fetch_weather"


def _route_after_weather(state: AdvisoryState) -> str:
    """Branch after weather fetch."""
    if state.get("error") == "WEATHER_UNAVAILABLE":
        return "weather_failure"
    return "evaluate_sops"


def _route_after_sop_eval(state: AdvisoryState) -> str:
    """Branch after SOP evaluation — match vs no-match."""
    matched = state.get("matched_sops", [])
    if matched:
        return "resolve_conflicts"
    return "no_sop_fallback"


def build_graph() -> StateGraph:
    """Build and compile the advisory LangGraph."""
    graph = StateGraph(AdvisoryState)

    # ── Add nodes ──
    graph.add_node("classify_intent", classify_intent)
    graph.add_node("resolve_location", resolve_location)
    graph.add_node("fetch_weather", fetch_weather)
    graph.add_node("evaluate_sops", evaluate_sops)
    graph.add_node("resolve_conflicts", resolve_conflicts_node)
    graph.add_node("compose_response", compose_response)
    graph.add_node("location_failure", location_failure)
    graph.add_node("weather_failure", weather_failure)
    graph.add_node("no_sop_fallback", no_sop_fallback)

    # ── Entry point ──
    graph.set_entry_point("classify_intent")

    # ── Edges ──
    graph.add_edge("classify_intent", "resolve_location")

    # Conditional: location success → fetch_weather | failure → location_failure
    graph.add_conditional_edges(
        "resolve_location",
        _route_after_location,
        {
            "fetch_weather": "fetch_weather",
            "location_failure": "location_failure",
        },
    )

    # Conditional: weather success → evaluate_sops | failure → weather_failure
    graph.add_conditional_edges(
        "fetch_weather",
        _route_after_weather,
        {
            "evaluate_sops": "evaluate_sops",
            "weather_failure": "weather_failure",
        },
    )

    # After SOP evaluation → resolve conflicts or fallback
    graph.add_conditional_edges(
        "evaluate_sops",
        _route_after_sop_eval,
        {
            "resolve_conflicts": "resolve_conflicts",
            "no_sop_fallback": "no_sop_fallback",
        },
    )

    # resolve_conflicts → compose_response
    graph.add_edge("resolve_conflicts", "compose_response")

    # Terminal edges
    graph.add_edge("compose_response", END)
    graph.add_edge("location_failure", END)
    graph.add_edge("weather_failure", END)
    graph.add_edge("no_sop_fallback", END)

    return graph.compile()


# Pre-compiled graph instance
advisory_graph = build_graph()
