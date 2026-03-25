"""LangGraph definition for the research document workflow."""

from typing import Any, Dict
from langgraph.graph import END, StateGraph
from src.nodes import (
    compilation_node,
    editing_node,
    error_node,
    planning_node,
    research_node,
    revision_node,
    should_continue_to_editing,
    should_continue_to_research,
    writing_node,
)
from src.state import ResearchState

def build_research_graph() -> StateGraph:
    """Build the simplified research document generation graph."""
    workflow = StateGraph(state_schema=ResearchState)

    # Add nodes
    workflow.add_node("planning", planning_node)
    workflow.add_node("research", research_node)
    workflow.add_node("writing", writing_node)
    workflow.add_node("editing", editing_node)
    workflow.add_node("revision", revision_node)
    workflow.add_node("compilation", compilation_node)
    workflow.add_node("error", error_node)

    # Set entry point
    workflow.set_entry_point("planning")

    # Add edges
    workflow.add_conditional_edges(
        "planning",
        should_continue_to_research,
        {"research": "research", "error": "error"}
    )

    workflow.add_edge("research", "writing")
    workflow.add_edge("writing", "editing")

    # Editing -> conditional (Go to revision or compilation)
    workflow.add_conditional_edges(
        "editing",
        should_continue_to_editing,
        {
            "revision": "revision", 
            "compiling": "compilation", 
            "error": "error"
        }
    )

    # Revision loops back to editing
    workflow.add_edge("revision", "editing")

    workflow.add_edge("compilation", END)
    workflow.add_edge("error", END)

    return workflow

def create_workflow(checkpointer=None) -> Any:
    """Create compiled workflow."""
    graph = build_research_graph()
    if checkpointer: return graph.compile(checkpointer=checkpointer)
    return graph.compile()
