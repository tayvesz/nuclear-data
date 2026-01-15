"""
RAG Tools - Document Retrieval and Search

Tools for vector search and document metadata retrieval.
"""

from typing import Dict, Any, List, Optional
from langchain.tools import tool
import streamlit as st


@tool
def search_technical_docs(query: str, k: int = 5) -> List[Dict[str, Any]]:
    """
    Recherche vectorielle dans les documents techniques.
    
    Args:
        query: Requête de recherche en langage naturel
        k: Nombre de résultats à retourner (défaut: 5)
        
    Returns:
        Liste de documents avec contenu, métadonnées et scores
    """
    vectorstore = st.session_state.get("vectorstore")
    
    if vectorstore is None:
        return [{
            "content": "❌ Base de connaissances non initialisée.",
            "metadata": {"source": "system"},
            "score": 0.0,
            "error": True
        }]
    
    try:
        results = vectorstore.similarity_search_with_score(query, k=k)
        
        documents = []
        for doc, score in results:
            documents.append({
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": float(score),
                "error": False
            })
        
        return documents
        
    except Exception as e:
        return [{
            "content": f"Erreur: {str(e)}",
            "metadata": {"source": "error"},
            "score": 0.0,
            "error": True
        }]


@tool
def get_doc_metadata(doc_id: str) -> Dict[str, Any]:
    """
    Récupère les métadonnées complètes d'un document.
    
    Args:
        doc_id: Identifiant ou nom du document
        
    Returns:
        Dictionnaire avec les métadonnées (auteur, date, version, type, etc.)
    """
    vectorstore = st.session_state.get("vectorstore")
    
    if vectorstore is None:
        return {"error": "Base de connaissances non initialisée"}
    
    try:
        # Search for documents matching the ID
        results = vectorstore.similarity_search(
            doc_id,
            k=10,
            filter={"source": {"$contains": doc_id}} if hasattr(vectorstore, '_collection') else None
        )
        
        if not results:
            return {"error": f"Document '{doc_id}' non trouvé"}
        
        # Aggregate metadata from matching chunks
        doc = results[0]
        metadata = {
            "source": doc.metadata.get("source", "Inconnu"),
            "page": doc.metadata.get("page", "N/A"),
            "doc_type": doc.metadata.get("doc_type", "document"),
            "timestamp_indexed": doc.metadata.get("timestamp_indexed", "N/A"),
            "chunk_count": len(results),
            "preview": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
        }
        
        return metadata
        
    except Exception as e:
        return {"error": str(e)}


def get_all_doc_types() -> List[str]:
    """Get all unique document types in the vectorstore."""
    vectorstore = st.session_state.get("vectorstore")
    
    if vectorstore is None:
        return []
    
    try:
        # This is ChromaDB specific
        if hasattr(vectorstore, '_collection'):
            results = vectorstore._collection.get()
            if results and "metadatas" in results:
                doc_types = set()
                for meta in results["metadatas"]:
                    if meta and "doc_type" in meta:
                        doc_types.add(meta["doc_type"])
                return list(doc_types)
        return ["procedure", "rapport", "specification"]
    except Exception:
        return ["procedure", "rapport", "specification"]


def filter_by_doc_type(query: str, doc_type: str, k: int = 5) -> List[Dict[str, Any]]:
    """
    Search with document type filter.
    
    Args:
        query: Search query
        doc_type: Type of document to filter (procedure, rapport, specification)
        k: Number of results
        
    Returns:
        List of filtered documents
    """
    vectorstore = st.session_state.get("vectorstore")
    
    if vectorstore is None:
        return []
    
    try:
        # ChromaDB filter syntax
        results = vectorstore.similarity_search_with_score(
            query,
            k=k,
            filter={"doc_type": doc_type}
        )
        
        return [
            {
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": float(score)
            }
            for doc, score in results
        ]
        
    except Exception as e:
        # Fallback to unfiltered search
        return search_technical_docs.invoke({"query": query, "k": k})
