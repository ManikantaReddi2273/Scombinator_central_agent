"""
Flow 1 LangGraph Workflow
Builds the state graph with all nodes and edges
"""
from langgraph.graph import StateGraph, END
from .state import Flow1State
from .nodes.classification_node import classification_node
from .nodes.priority_scorer_node import priority_scorer_node
from .nodes.summarizer_node import summarizer_node
from .nodes.action_recommender_node import action_recommender_node
from .nodes.draft_generator_node import draft_generator_node
from config import settings
import logging

logger = logging.getLogger(__name__)


def build_flow1_graph():
    """
    Build and compile the Flow 1 LangGraph workflow
    
    Returns:
        Compiled LangGraph with optional checkpointing
    """
    # Build graph
    workflow = StateGraph(Flow1State)
    
    # Add nodes (Steps 2-6)
    workflow.add_node("classify", classification_node)
    workflow.add_node("score_priority", priority_scorer_node)
    workflow.add_node("summarize", summarizer_node)
    workflow.add_node("recommend_action", action_recommender_node)
    workflow.add_node("generate_draft", draft_generator_node)
    
    # Define sequential edges
    workflow.set_entry_point("classify")
    workflow.add_edge("classify", "score_priority")
    workflow.add_edge("score_priority", "summarize")
    workflow.add_edge("summarize", "recommend_action")
    workflow.add_edge("recommend_action", "generate_draft")
    workflow.add_edge("generate_draft", END)
    
    # Try to compile with checkpointing (optional)
    try:
        # Try different import paths for checkpointing
        try:
            from langgraph.checkpoint.postgres import PostgresSaver
            checkpointer = PostgresSaver.from_conn_string(settings.LANGRAPH_CHECKPOINT_DB_URL)
            flow1_graph = workflow.compile(checkpointer=checkpointer)
            logger.info("Flow 1 graph compiled successfully with PostgreSQL checkpointing")
            return flow1_graph
        except ImportError:
            # Try alternative import path
            try:
                from langgraph.checkpoint import PostgresSaver
                checkpointer = PostgresSaver.from_conn_string(settings.LANGRAPH_CHECKPOINT_DB_URL)
                flow1_graph = workflow.compile(checkpointer=checkpointer)
                logger.info("Flow 1 graph compiled successfully with PostgreSQL checkpointing")
                return flow1_graph
            except ImportError:
                # Checkpointing not available in this version
                logger.warning("PostgreSQL checkpointing not available in this LangGraph version. Compiling without checkpointing.")
                flow1_graph = workflow.compile()
                return flow1_graph
    except Exception as e:
        logger.error(f"Error setting up checkpointing: {str(e)}")
        # Fallback: compile without checkpointing (for development)
        logger.warning("Compiling graph without checkpointing (checkpoint DB may not be available)")
        flow1_graph = workflow.compile()
        return flow1_graph


# Create graph instance
flow1_graph = build_flow1_graph()

