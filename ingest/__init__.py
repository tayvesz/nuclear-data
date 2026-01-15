"""
Ingest package - Data Pipeline Scripts for Framatome AI Assistant

This package contains all data ingestion scripts:
- build_vectorstore: Create ChromaDB from documents
- seed_operational_db: Generate operational database
- build_complete_dataset: Full pipeline with real data
- download_documents: Fetch public documents for RAG
"""

from .build_vectorstore import build_vectorstore, load_vectorstore
from .seed_operational_db import seed_database, load_operational_data, get_db_summary
from .build_complete_dataset import build_complete_dataset, download_geonuclear_data
from .download_documents import setup_document_corpus, create_demo_documents

__all__ = [
    # Vector store
    "build_vectorstore",
    "load_vectorstore",
    
    # Operational database
    "seed_database",
    "load_operational_data",
    "get_db_summary",
    
    # Complete dataset
    "build_complete_dataset",
    "download_geonuclear_data",
    
    # Documents
    "setup_document_corpus",
    "create_demo_documents",
]


def run_full_ingestion(
    db_path: str = "data/operational.db",
    docs_dir: str = "data/docs",
    vectorstore_dir: str = "data/vectorstore",
    years: int = 10,
    download_external: bool = False
) -> dict:
    """
    Run the complete data ingestion pipeline.
    
    Args:
        db_path: Path for SQLite database
        docs_dir: Directory for documents
        vectorstore_dir: Directory for ChromaDB
        years: Years of historical data
        download_external: Whether to download external documents
        
    Returns:
        Summary of ingestion results
    """
    print("\n" + "="*60)
    print("🚀 FRAMATOME AI ASSISTANT - FULL INGESTION PIPELINE")
    print("="*60 + "\n")
    
    results = {}
    
    # Step 1: Create operational database
    print("\n📊 Step 1/3: Building operational database...")
    try:
        db_summary = build_complete_dataset(
            db_path=db_path,
            years=years,
            download_docs=False  # Handle docs separately
        )
        results["database"] = db_summary
    except Exception as e:
        print(f"  ✗ Database error: {e}")
        results["database"] = {"error": str(e)}
    
    # Step 2: Setup document corpus
    print("\n📚 Step 2/3: Setting up document corpus...")
    try:
        doc_summary = setup_document_corpus(
            output_dir=docs_dir,
            include_downloads=download_external
        )
        results["documents"] = doc_summary
    except Exception as e:
        print(f"  ✗ Document error: {e}")
        results["documents"] = {"error": str(e)}
    
    # Step 3: Build vector store
    print("\n🧮 Step 3/3: Building vector store...")
    try:
        vectorstore = build_vectorstore(
            docs_dir=docs_dir,
            persist_dir=vectorstore_dir
        )
        results["vectorstore"] = {
            "success": vectorstore is not None,
            "path": vectorstore_dir
        }
    except Exception as e:
        print(f"  ✗ Vector store error: {e}")
        results["vectorstore"] = {"error": str(e)}
    
    # Summary
    print("\n" + "="*60)
    print("✅ INGESTION COMPLETE")
    print("="*60)
    
    return results
