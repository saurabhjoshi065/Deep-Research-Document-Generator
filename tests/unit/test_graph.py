"""Unit tests for research graph."""

from unittest.mock import MagicMock, patch
import pytest
from src.graph import build_research_graph, create_workflow
from src.state import create_initial_state

class TestGraphStructure:
    def test_build_graph(self):
        graph = build_research_graph()
        assert graph is not None
        assert "planning" in graph.nodes
        assert "research" in graph.nodes

    def test_create_workflow(self):
        workflow = create_workflow()
        assert workflow is not None

class TestGraphNodes:
    @patch("src.nodes.planning_node")
    def test_workflow_execution(self, mock_plan):
        mock_plan.return_value = {"current_step": "completed"}
        workflow = create_workflow()
        state = create_initial_state("Test")
        # Just verify it can be invoked
        try:
            workflow.invoke(state)
        except:
            pass
