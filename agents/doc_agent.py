"""
Document Agent (DocAgent) - RAG-based Document Retrieval

Specializes in:
- Technical documentation search
- Procedure retrieval
- Safety regulations lookup
- Inspection reports analysis
"""

from typing import Dict, Any, List
from langchain_core.messages import HumanMessage, SystemMessage
import streamlit as st

# Import centralized LLM config
from .llm_config import get_llm


DOC_AGENT_SYSTEM_PROMPT = """Tu es un expert en documentation technique nucléaire pour Framatome.

Ton rôle est de rechercher et analyser les documents techniques pour répondre aux questions.

INSTRUCTIONS:
1. Utilise la recherche vectorielle pour trouver les documents pertinents
2. Cite TOUJOURS tes sources avec le nom du document et le numéro de page
3. Si l'information n'est pas trouvée, dis-le clairement
4. Fournis des réponses précises et techniques
5. Structure ta réponse avec des sections claires

FORMAT DE RÉPONSE:
- Réponse principale avec les informations techniques
- Liste des sources utilisées avec scores de pertinence
"""




def search_documents(query: str, k: int = 5) -> List[Dict[str, Any]]:
    """
    Search the vector store for relevant documents.
    
    Args:
        query: Search query
        k: Number of results to return
        
    Returns:
        List of document chunks with metadata and scores
    """
    vectorstore = st.session_state.get("vectorstore")
    
    if vectorstore is None:
        return [{
            "content": "Base de connaissances non initialisée. Veuillez charger les documents.",
            "metadata": {"source": "system", "page": 0},
            "score": 0.0
        }]
    
    try:
        # Perform similarity search with scores
        results = vectorstore.similarity_search_with_score(query, k=k)
        
        documents = []
        for doc, score in results:
            documents.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": float(score)
            })
        
        return documents
        
    except Exception as e:
        return [{
            "content": f"Erreur lors de la recherche: {str(e)}",
            "metadata": {"source": "error", "page": 0},
            "score": 0.0
        }]


def format_sources(documents: List[Dict[str, Any]]) -> str:
    """Format document sources for display."""
    sources_text = "\n\n📚 **Sources consultées:**\n"
    for i, doc in enumerate(documents, 1):
        source = doc["metadata"].get("source", "Document inconnu")
        page = doc["metadata"].get("page", "N/A")
        score = doc["score"]
        # Lower score is better for ChromaDB L2 distance
        relevance = "🟢" if score < 0.5 else "🟡" if score < 1.0 else "🔴"
        sources_text += f"{i}. {relevance} **{source}** (p.{page}) - score: {score:.3f}\n"
    
    return sources_text


def doc_agent_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Document retrieval agent node.
    
    Performs RAG search and generates response with citations.
    """
    question = state["messages"][-1] if state["messages"] else ""
    
    # Search for relevant documents
    documents = search_documents(question, k=5)
    
    # Build context from documents
    context = "\n\n---\n\n".join([
        f"[Source: {doc['metadata'].get('source', 'N/A')}, Page: {doc['metadata'].get('page', 'N/A')}]\n{doc['content']}"
        for doc in documents
    ])
    
    # Generate response with LLM
    llm = get_llm()
    
    rag_prompt = f"""Contexte documentaire:
{context}

Question de l'utilisateur: {question}

En te basant UNIQUEMENT sur le contexte fourni, réponds à la question.
Si l'information n'est pas dans le contexte, dis-le clairement.
Cite les sources pertinentes dans ta réponse."""
    
    try:
        response = llm.invoke([
            SystemMessage(content=DOC_AGENT_SYSTEM_PROMPT),
            HumanMessage(content=rag_prompt)
        ])
        
        answer = response.content
        
        # Add formatted sources
        answer += format_sources(documents)
        
    except Exception as e:
        answer = f"❌ Erreur lors de la génération de la réponse: {str(e)}"
        documents = []
    
    return {
        "doc_results": {
            "answer": answer,
            "sources": documents,
            "query": question
        },
        "messages": [f"[DocAgent] {answer}"],
        "final_answer": answer
    }
