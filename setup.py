#!/usr/bin/env python3
"""
🚀 Quick Setup Script for Framatome AI Assistant

This script initializes all data required to run the application:
1. Creates the operational database with simulated data
2. Sets up the document corpus (demo + optional downloads)
3. Builds the ChromaDB vector store

Usage:
    python setup.py              # Full setup with demo data
    python setup.py --full       # Include external document downloads
    python setup.py --db-only    # Only create database
    python setup.py --docs-only  # Only setup documents
"""

import argparse
import sys
from pathlib import Path

# Ensure we're in the right directory
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def setup_database(years: int = 10):
    """Create the operational database."""
    print("\n" + "="*50)
    print("📊 SETTING UP OPERATIONAL DATABASE")
    print("="*50)
    
    from ingest.build_complete_dataset import build_complete_dataset
    
    return build_complete_dataset(
        db_path="data/operational.db",
        years=years,
        download_docs=False
    )


def setup_documents(include_downloads: bool = False):
    """Setup document corpus."""
    print("\n" + "="*50)
    print("📚 SETTING UP DOCUMENT CORPUS")
    print("="*50)
    
    from ingest.download_documents import setup_document_corpus
    
    return setup_document_corpus(
        output_dir="data/docs",
        include_downloads=include_downloads
    )


def setup_vectorstore():
    """Build the vector store."""
    print("\n" + "="*50)
    print("🧮 BUILDING VECTOR STORE")
    print("="*50)
    
    from ingest.build_vectorstore import build_vectorstore
    
    return build_vectorstore(
        docs_dir="data/docs",
        persist_dir="data/vectorstore"
    )


def check_api_key():
    """Check if OpenAI API key is configured."""
    import os
    
    # Check environment variable
    if os.getenv("OPENAI_API_KEY"):
        return True
    
    # Check Streamlit secrets
    secrets_path = Path(".streamlit/secrets.toml")
    if secrets_path.exists():
        content = secrets_path.read_text()
        if "api_key" in content and "sk-" in content:
            return True
    
    return False


def main():
    parser = argparse.ArgumentParser(
        description="Setup Framatome AI Assistant data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python setup.py                    # Quick setup with demo data
  python setup.py --full             # Full setup with external downloads
  python setup.py --db-only          # Only create database
  python setup.py --years 5          # 5 years of historical data
        """
    )
    
    parser.add_argument(
        "--full", 
        action="store_true",
        help="Include external document downloads (NRC, IAEA)"
    )
    parser.add_argument(
        "--db-only",
        action="store_true", 
        help="Only create operational database"
    )
    parser.add_argument(
        "--docs-only",
        action="store_true",
        help="Only setup documents (no vector store)"
    )
    parser.add_argument(
        "--vectorstore-only",
        action="store_true",
        help="Only build vector store (documents must exist)"
    )
    parser.add_argument(
        "--years",
        type=int,
        default=10,
        help="Years of historical data to generate (default: 10)"
    )
    parser.add_argument(
        "--skip-api-check",
        action="store_true",
        help="Skip OpenAI API key check"
    )
    
    args = parser.parse_args()
    
    print("""
╔═══════════════════════════════════════════════════════════╗
║  🏭 FRAMATOME AI ASSISTANT - SETUP                        ║
║  Multi-Agent RAG System for Nuclear Plant Operations      ║
╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Check API key for vector store operations
    if not args.db_only and not args.skip_api_check:
        if not check_api_key():
            print("⚠️  WARNING: OpenAI API key not found!")
            print("   Vector store creation requires an API key.")
            print("   Please set OPENAI_API_KEY environment variable or")
            print("   configure .streamlit/secrets.toml")
            print("\n   To skip this check, use --skip-api-check")
            print("   To only create database, use --db-only\n")
            
            response = input("Continue anyway? [y/N]: ")
            if response.lower() != 'y':
                sys.exit(1)
    
    results = {}
    
    try:
        # Database
        if not args.docs_only and not args.vectorstore_only:
            results["database"] = setup_database(years=args.years)
        
        # Documents
        if not args.db_only and not args.vectorstore_only:
            results["documents"] = setup_documents(include_downloads=args.full)
        
        # Vector store
        if not args.db_only and not args.docs_only:
            results["vectorstore"] = setup_vectorstore()
        
        # Final summary
        print("\n" + "="*60)
        print("✅ SETUP COMPLETE!")
        print("="*60)
        print("""
Next steps:
  1. Configure your API key in .streamlit/secrets.toml
  2. Run the application: streamlit run app.py
  3. Open http://localhost:8501 in your browser
  
Example questions to try:
  • "Combien de réacteurs sont opérationnels en France ?"
  • "Quelle est la procédure de maintenance des pompes ?"
  • "Graphique des maintenances par type d'équipement"
  • "Statistiques des incidents par sévérité"
        """)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
