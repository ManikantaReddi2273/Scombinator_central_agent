"""
Flow 2 LangGraph Workflow
Builds the state graph with all nodes and edges
"""
from langgraph.graph import StateGraph, END
from .state import Flow2State
from .nodes.intent_definition_node import intent_definition_node
from .nodes.recipient_context_node import recipient_context_node
from .nodes.template_selection_node import template_selection_node
from .nodes.draft_generator_node import draft_generator_node
from config import settings
import logging

logger = logging.getLogger(__name__)


def build_flow2_graph():
    """
    Build and compile the Flow 2 LangGraph workflow
    
    Returns:
        Compiled LangGraph with optional checkpointing
    """
    # Build graph
    workflow = StateGraph(Flow2State)
    
    # Add nodes (Steps 1-4)
    workflow.add_node("intent_definition", intent_definition_node)
    workflow.add_node("enrich_recipient_context", recipient_context_node)
    workflow.add_node("template_selection", template_selection_node)
    workflow.add_node("draft_generator", draft_generator_node)
    
    # Define sequential edges
    workflow.set_entry_point("intent_definition")
    workflow.add_edge("intent_definition", "enrich_recipient_context")
    workflow.add_edge("enrich_recipient_context", "template_selection")
    workflow.add_edge("template_selection", "draft_generator")
    workflow.add_edge("draft_generator", END)
    
    # Try to compile with checkpointing (optional)
    try:
        if hasattr(settings, 'LANGGRAPH_CHECKPOINT') and settings.LANGGRAPH_CHECKPOINT:
            # In production, add checkpointing for state persistence
            workflow = workflow.compile(checkpointer=settings.LANGGRAPH_CHECKPOINT)
        else:
            workflow = workflow.compile()
    except Exception as e:
        logger.warning(f"Could not compile with checkpointing: {str(e)}. Using basic compilation.")
        workflow = workflow.compile()
    
    return workflow


# Build graph on module import
flow2_graph = build_flow2_graph()

