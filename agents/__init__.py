"""
Multi-Agent System for Framatome AI Assistant

This package contains specialized agents for:
- DocAgent: RAG-based document retrieval
- DataAgent: SQL/statistics analysis
- VizAgent: Plotly visualization generation
- SummaryAgent: Multi-source synthesis
"""

from .supervisor import create_supervisor_graph, AgentState
from .doc_agent import doc_agent_node
from .data_agent import data_agent_node
from .viz_agent import viz_agent_node
from .summary_agent import summary_agent_node

__all__ = [
    "create_supervisor_graph",
    "AgentState",
    "doc_agent_node",
    "data_agent_node",
    "viz_agent_node",
    "summary_agent_node",
]
