"""
Supervisor Agent - LangGraph Router

Orchestrates the multi-agent system by routing user queries
to the appropriate specialized agent.
"""

from typing import TypedDict, Annotated, Sequence, Literal, Any, Optional
import operator
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
import streamlit as st

# Import centralized LLM config
from .llm_config import get_llm


class AgentState(TypedDict):
    """State shared between all agents in the graph."""
    messages: Annotated[Sequence[str], operator.add]
    next_agent: str
    doc_results: dict
    data_results: dict
    viz_results: dict
    final_answer: str
    error: Optional[str]


def route_question(state: AgentState) -> dict:
    """
    LLM-based router that decides which agent to invoke.
    
    Routing logic:
    - DocAgent: Documentation, procedures, regulations
    - DataAgent: Quantitative queries, statistics, counts
    - VizAgent: Explicit visualization requests
    - SummaryAgent: Complex multi-source questions
    """
    llm = get_llm()
    
    question = state["messages"][-1] if state["messages"] else ""
    
    routing_prompt = f"""Tu es un routeur intelligent pour un système multi-agent industriel nucléaire.

Question de l'utilisateur: {question}

Analyse la question et choisis L'UNIQUE agent le plus approprié:

1. **DocAgent** - Pour les questions sur:
   - Procédures techniques et documentation
   - Réglementation et normes de sécurité
   - Spécifications et guides opérationnels
   - Historique des inspections et rapports

2. **DataAgent** - Pour les questions sur:
   - Comptages et statistiques (combien, nombre de, total)
   - Données opérationnelles et métriques
   - Analyses de tendances avec chiffres
   - Requêtes sur la base de données

3. **VizAgent** - Pour les demandes explicites de:
   - Graphiques et visualisations
   - Courbes, histogrammes, diagrammes
   - Représentations visuelles de données

4. **SummaryAgent** - Pour:
   - Synthèses globales multi-sources
   - Questions complexes nécessitant plusieurs agents
   - Résumés exécutifs

Réponds UNIQUEMENT par le nom de l'agent (DocAgent, DataAgent, VizAgent, ou SummaryAgent).
"""
    
    try:
        response = llm.invoke([HumanMessage(content=routing_prompt)])
        agent = response.content.strip()
        
        # Validate agent name
        valid_agents = ["DocAgent", "DataAgent", "VizAgent", "SummaryAgent"]
        if agent not in valid_agents:
            # Default to DocAgent if unrecognized
            agent = "DocAgent"
            
    except Exception as e:
        # Fallback routing based on keywords
        question_lower = question.lower()
        if any(word in question_lower for word in ["graphique", "courbe", "visualis", "plot", "chart", "diagramme"]):
            agent = "VizAgent"
        elif any(word in question_lower for word in ["combien", "nombre", "total", "statistique", "moyenne", "tendance"]):
            agent = "DataAgent"
        elif any(word in question_lower for word in ["synthèse", "résumé", "global", "récapitul"]):
            agent = "SummaryAgent"
        else:
            agent = "DocAgent"
    
    return {"next_agent": agent}


def should_continue(state: AgentState) -> Literal["DocAgent", "DataAgent", "VizAgent", "SummaryAgent"]:
    """Conditional edge function to route to the appropriate agent."""
    return state["next_agent"]


def create_supervisor_graph():
    """
    Create and compile the LangGraph supervisor workflow.
    
    Architecture:
        User Question
             ↓
         Supervisor (Router)
             ↓
       ┌─────────────┬──────────────┬──────────────┐
       ↓             ↓              ↓              ↓
    DocAgent    DataAgent      VizAgent      SummaryAgent
       ↓             ↓              ↓              ↓
       └─────────────┴──────────────┘              │
                     ↓                             │
              SummaryAgent ←───────────────────────┘
                     ↓
                   END
    """
    from .doc_agent import doc_agent_node
    from .data_agent import data_agent_node
    from .viz_agent import viz_agent_node
    from .summary_agent import summary_agent_node
    
    # Build the graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("router", route_question)
    workflow.add_node("DocAgent", doc_agent_node)
    workflow.add_node("DataAgent", data_agent_node)
    workflow.add_node("VizAgent", viz_agent_node)
    workflow.add_node("SummaryAgent", summary_agent_node)
    
    # Set entry point
    workflow.set_entry_point("router")
    
    # Add conditional edges from router
    workflow.add_conditional_edges(
        "router",
        should_continue,
        {
            "DocAgent": "DocAgent",
            "DataAgent": "DataAgent",
            "VizAgent": "VizAgent",
            "SummaryAgent": "SummaryAgent",
        }
    )
    
    # DocAgent and DataAgent go to SummaryAgent for synthesis
    workflow.add_edge("DocAgent", "SummaryAgent")
    workflow.add_edge("DataAgent", "SummaryAgent")
    
    # VizAgent goes directly to END (no need for summary)
    workflow.add_edge("VizAgent", END)
    
    # SummaryAgent is the final step
    workflow.add_edge("SummaryAgent", END)
    
    # Compile the graph
    app = workflow.compile()
    
    return app


# Create a default instance
def get_supervisor():
    """Get or create the supervisor graph (cached in session state)."""
    if "supervisor_graph" not in st.session_state:
        st.session_state.supervisor_graph = create_supervisor_graph()
    return st.session_state.supervisor_graph
