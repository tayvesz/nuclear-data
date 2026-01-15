"""
🏭 Framatome AI Assistant - Multi-Agent Industrial Assistant

A sophisticated multi-agent system for nuclear plant documentation
and operational data analysis.

Architecture:
- DocAgent: RAG-based document retrieval
- DataAgent: SQL/statistics analysis  
- VizAgent: Plotly visualization generation
- SummaryAgent: Multi-source synthesis
"""

import streamlit as st
from pathlib import Path
import json
from datetime import datetime
import os
import sys

# Fix pour ChromaDB sur Streamlit Cloud (SQLite version)
try:
    __import__('pysqlite3')
    import sys
    sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
except ImportError:
    pass


# Page configuration
st.set_page_config(
    page_title="☢️ Chatbot Données Nucléaires",
    page_icon="☢️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for premium look
st.markdown("""
<style>
    /* Main theme */
    .stApp {
        background: linear-gradient(180deg, #0E1117 0%, #1a1f2e 100%);
    }
    
    /* Chat messages */
    .stChatMessage {
        background: rgba(38, 39, 48, 0.8);
        border-radius: 12px;
        padding: 1rem;
        margin: 0.5rem 0;
        border: 1px solid rgba(255,255,255,0.1);
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: linear-gradient(180deg, #1a1f2e 0%, #0E1117 100%);
    }
    
    /* Headers */
    h1, h2, h3 {
        background: linear-gradient(90deg, #0066CC 0%, #00A3FF 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(90deg, #0066CC 0%, #0088FF 100%);
        border: none;
        border-radius: 8px;
        color: white;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 20px rgba(0, 102, 204, 0.4);
    }
    
    /* Info boxes */
    .info-box {
        background: rgba(0, 102, 204, 0.1);
        border-left: 4px solid #0066CC;
        padding: 1rem;
        border-radius: 0 8px 8px 0;
        margin: 1rem 0;
    }
    
    /* Framatome Logo */
    .framatome-logo {
        font-size: 1.8rem;
        font-weight: 800;
        background: linear-gradient(90deg, #E31937 0%, #0066CC 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        letter-spacing: -0.5px;
        margin-bottom: 0.5rem;
    }
    
    /* Starter prompts */
    .starter-prompt {
        background: rgba(0, 102, 204, 0.1);
        border: 1px solid rgba(0, 102, 204, 0.3);
        border-radius: 12px;
        padding: 1rem;
        margin: 0.5rem 0;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .starter-prompt:hover {
        background: rgba(0, 102, 204, 0.2);
        border-color: #0066CC;
        transform: translateX(5px);
    }
    
    .starter-icon {
        font-size: 1.5rem;
        margin-right: 0.5rem;
    }
    
    /* Agent badges */
    .agent-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        margin-right: 0.5rem;
    }
    
    .agent-doc { background: rgba(46, 204, 113, 0.2); color: #2ECC71; }
    .agent-data { background: rgba(52, 152, 219, 0.2); color: #3498DB; }
    .agent-viz { background: rgba(155, 89, 182, 0.2); color: #9B59B6; }
    .agent-summary { background: rgba(241, 196, 15, 0.2); color: #F1C40F; }
    
    /* Metric cards */
    .metric-card {
        background: rgba(255,255,255,0.05);
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        border: 1px solid rgba(255,255,255,0.1);
        transition: all 0.3s ease;
    }
    
    .metric-card:hover {
        border-color: #0066CC;
        transform: translateY(-2px);
    }
    
    /* Source citations */
    .source-citation {
        font-size: 0.85rem;
        color: #888;
        padding: 0.5rem;
        background: rgba(0,0,0,0.2);
        border-radius: 4px;
        margin: 0.25rem 0;
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #1a1f2e;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #0066CC;
        border-radius: 4px;
    }
    
    /* Code blocks */
    .stCodeBlock {
        border-radius: 8px;
        border: 1px solid rgba(255,255,255,0.1);
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: rgba(255,255,255,0.05);
        border-radius: 8px;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize Streamlit session state variables."""
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    if "db_path" not in st.session_state:
        st.session_state.db_path = "data/operational.db"
    
    if "vectorstore" not in st.session_state:
        st.session_state.vectorstore = None
    
    if "supervisor_graph" not in st.session_state:
        st.session_state.supervisor_graph = None
    
    if "interaction_log" not in st.session_state:
        st.session_state.interaction_log = []


def load_resources():
    """Load vector store and database on startup."""
    from ingest.build_vectorstore import load_vectorstore, build_vectorstore
    from ingest.seed_operational_db import seed_database, load_operational_data
    
    # Load or create vector store
    if st.session_state.vectorstore is None:
        vs = load_vectorstore("data/vectorstore")
        if vs is None:
            with st.spinner("🔧 Building vector store with demo documents..."):
                vs = build_vectorstore()
        st.session_state.vectorstore = vs
    
    # Load or create database
    db_path = Path(st.session_state.db_path)
    if not db_path.exists():
        with st.spinner("🔧 Creating operational database..."):
            seed_database(str(db_path))
    
    # Load data into session
    if "operational_data" not in st.session_state:
        data = load_operational_data(str(db_path))
        st.session_state.operational_data = data.get("maintenances")


def get_supervisor():
    """Get or create the supervisor graph."""
    if st.session_state.supervisor_graph is None:
        from agents.supervisor import create_supervisor_graph
        st.session_state.supervisor_graph = create_supervisor_graph()
    return st.session_state.supervisor_graph


def log_interaction(question: str, result: dict):
    """Log interaction for traceability."""
    st.session_state.interaction_log.append({
        "timestamp": datetime.now().isoformat(),
        "question": question,
        "agent_used": result.get("next_agent", "Unknown"),
        "success": bool(result.get("final_answer"))
    })


def render_sidebar():
    """Render the sidebar with configuration and info."""
    with st.sidebar:
        # Logo styled (works offline)
        st.markdown('''
        <div style="
            background: linear-gradient(135deg, #FFA500 0%, #00CED1 100%);
            -webkit-background-clip: text;
            background-clip: text;
            -webkit-text-fill-color: transparent;
            font-size: 1.6rem;
            font-weight: 800;
            letter-spacing: -1px;
            margin-bottom: 0.5rem;
            padding: 0.5rem 0;
        ">☢️ Nucléaire AI</div>
        ''', unsafe_allow_html=True)
        st.title("Chatbot Données")
        st.caption("Assistant IA Multi-Agent - Données Nucléaires")
        
        st.divider()
        
        # Agent info
        st.subheader("🤖 Agents Disponibles")
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**📄 DocAgent**")
            st.caption("RAG documentaire")
            
            st.markdown("**📊 DataAgent**")  
            st.caption("SQL & statistiques")
        
        with col2:
            st.markdown("**📈 VizAgent**")
            st.caption("Visualisations")
            
            st.markdown("**📝 Summary**")
            st.caption("Synthèse")
        
        st.divider()
        
        # Database info
        st.subheader("📊 Base de Données")
        
        try:
            from ingest.seed_operational_db import get_db_summary
            summary = get_db_summary(st.session_state.db_path)
            st.code(summary, language=None)
        except Exception as e:
            st.warning("Base non chargée")
        
        st.divider()
        
        # Actions
        st.subheader("⚙️ Actions")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Reload", use_container_width=True):
                st.session_state.vectorstore = None
                st.session_state.supervisor_graph = None
                st.rerun()
        
        with col2:
            if st.button("🗑️ Clear", use_container_width=True):
                st.session_state.messages = []
                st.rerun()
        
        # Example questions
        st.divider()
        st.subheader("💡 Exemples")
        
        examples = [
            "Combien de réacteurs sont opérationnels ?",
            "Quelle est la procédure de maintenance des pompes ?",
            "Graphique des maintenances par type",
            "Statistiques des incidents par sévérité",
        ]
        
        for example in examples:
            if st.button(f"📌 {example[:35]}...", key=f"ex_{hash(example)}", use_container_width=True):
                st.session_state.pending_question = example
                st.rerun()


def render_message(msg: dict):
    """Render a chat message with enhanced formatting."""
    role = msg["role"]
    content = msg["content"]
    
    avatar = "👤" if role == "user" else "🤖"
    
    with st.chat_message(role, avatar=avatar):
        st.markdown(content)
        
        # Display figure if present
        if "figure" in msg and msg["figure"] is not None:
            st.plotly_chart(msg["figure"], use_container_width=True)
            
            if "code" in msg:
                with st.expander("💻 Code Python Reproductible"):
                    st.code(msg["code"], language="python")
        
        # Display sources if present
        if "sources" in msg and msg["sources"]:
            with st.expander("📚 Sources Documentaires"):
                for src in msg["sources"]:
                    source = src.get("metadata", {}).get("source", "N/A")
                    page = src.get("metadata", {}).get("page", "N/A")
                    score = src.get("score", 0)
                    relevance = "🟢" if score < 0.5 else "🟡" if score < 1.0 else "🔴"
                    st.caption(f"{relevance} **{source}** (p.{page}) - score: {score:.3f}")


def process_question(question: str) -> dict:
    """Process a user question through the multi-agent system."""
    supervisor = get_supervisor()
    
    initial_state = {
        "messages": [question],
        "next_agent": "",
        "doc_results": {},
        "data_results": {},
        "viz_results": {},
        "final_answer": "",
        "error": None
    }
    
    try:
        result = supervisor.invoke(initial_state)
        return result
    except Exception as e:
        return {
            "final_answer": f"❌ Erreur système: {str(e)}",
            "error": str(e),
            "viz_results": {},
            "doc_results": {}
        }


def main():
    """Main application entry point."""
    init_session_state()
    
    # Render sidebar
    render_sidebar()
    
    # Main content
    st.title("☢️ Chatbot Données Nucléaires")
    st.caption("Assistant IA Multi-Agent | Documentation & Données opérationnelles")
    
    # Load resources
    with st.spinner("⏳ Chargement des ressources..."):
        try:
            load_resources()
        except Exception as e:
            st.error(f"Erreur de chargement: {e}")
            st.info("Vérifiez que les clés API sont configurées dans `.streamlit/secrets.toml`")
            return
    
    # Welcome message with starter prompts
    if not st.session_state.messages:
        st.markdown("""
        <div class="info-box">
            <h4>👋 Bienvenue !</h4>
            <p>Je suis votre assistant IA spécialisé en maintenance industrielle nucléaire.</p>
            <p>Je peux vous aider à :</p>
            <ul>
                <li>📄 <strong>Rechercher</strong> dans la documentation technique</li>
                <li>📊 <strong>Analyser</strong> les données opérationnelles</li>
                <li>📈 <strong>Visualiser</strong> les métriques et tendances</li>
                <li>📝 <strong>Synthétiser</strong> des informations multi-sources</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)
        
        # Starter prompts - clickable examples
        st.markdown("### 💡 Commencez par une question :")
        
        # Define starter prompts
        starters = [
            {"icon": "📊", "agent": "DataAgent", "question": "Combien de réacteurs sont opérationnels en France ?", "desc": "Analyse quantitative"},
            {"icon": "📄", "agent": "DocAgent", "question": "Quelle est la procédure de maintenance des pompes primaires ?", "desc": "Documentation technique"},
            {"icon": "📈", "agent": "VizAgent", "question": "Graphique des maintenances par type d'équipement", "desc": "Visualisation"},
            {"icon": "⚠️", "agent": "DataAgent", "question": "Statistiques des incidents par niveau de sévérité", "desc": "Analyse incidents"},
            {"icon": "🔧", "agent": "DataAgent", "question": "Durée moyenne des maintenances correctives vs préventives", "desc": "Comparaison"},
            {"icon": "📋", "agent": "DocAgent", "question": "Quels sont les critères de sûreté nucléaire (défense en profondeur) ?", "desc": "Réglementation"},
        ]
        
        # Define callback
        def set_question(q):
            st.session_state.pending_question = q
        
        # Display in 2 columns
        col1, col2 = st.columns(2)
        
        for i, starter in enumerate(starters):
            col = col1 if i % 2 == 0 else col2
            with col:
                st.button(
                    f"{starter['icon']} {starter['question'][:50]}{'...' if len(starter['question']) > 50 else ''}",
                    key=f"starter_{i}",
                    use_container_width=True,
                    help=f"{starter['desc']} → {starter['agent']}",
                    on_click=set_question,
                    args=(starter['question'],)
                )
    
    # Display chat history
    for msg in st.session_state.messages:
        render_message(msg)
    
    # Check for pending question from example buttons
    if "pending_question" in st.session_state:
        question = st.session_state.pending_question
        del st.session_state.pending_question
        
        # Add to messages
        st.session_state.messages.append({"role": "user", "content": question})
        render_message({"role": "user", "content": question})
        
        # Process
        with st.spinner("🤖 Agents en action..."):
            result = process_question(question)
        
        # Build response message
        response_msg = {
            "role": "assistant",
            "content": result.get("final_answer", "Pas de réponse générée.")
        }
        
        # Add viz if present
        viz_results = result.get("viz_results", {})
        if viz_results.get("success") and viz_results.get("figure"):
            response_msg["figure"] = viz_results["figure"]
            response_msg["code"] = viz_results.get("code")
        
        # Add sources if present
        doc_results = result.get("doc_results", {})
        if doc_results.get("sources"):
            response_msg["sources"] = doc_results["sources"]
        
        st.session_state.messages.append(response_msg)
        log_interaction(question, result)
        st.rerun()
    
    # Chat input
    if question := st.chat_input("Ex: Combien de maintenances préventives en 2024 ?"):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": question})
        render_message({"role": "user", "content": question})
        
        # Process through supervisor
        with st.spinner("🤖 Agents en action..."):
            result = process_question(question)
        
        # Build response message
        response_msg = {
            "role": "assistant",
            "content": result.get("final_answer", "Pas de réponse générée.")
        }
        
        # Add viz if present
        viz_results = result.get("viz_results", {})
        if viz_results.get("success") and viz_results.get("figure"):
            response_msg["figure"] = viz_results["figure"]
            response_msg["code"] = viz_results.get("code")
        
        # Add sources if present
        doc_results = result.get("doc_results", {})
        if doc_results.get("sources"):
            response_msg["sources"] = doc_results["sources"]
        
        st.session_state.messages.append(response_msg)
        log_interaction(question, result)
        st.rerun()


if __name__ == "__main__":
    main()
