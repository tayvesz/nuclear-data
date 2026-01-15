"""
Build Vector Store - Document Ingestion Pipeline

Processes PDF documents and builds a ChromaDB vector store.
"""

import os
from pathlib import Path
from datetime import datetime
from typing import List, Optional
import streamlit as st


def build_vectorstore(
    docs_dir: str = "data/docs",
    persist_dir: str = "data/vectorstore",
    chunk_size: int = 800,
    chunk_overlap: int = 150
) -> None:
    """
    Build a ChromaDB vector store from PDF/text documents.
    
    Args:
        docs_dir: Directory containing source documents
        persist_dir: Directory to persist the vector store
        chunk_size: Size of text chunks
        chunk_overlap: Overlap between chunks
    """
    from langchain_community.document_loaders import (
        PyPDFLoader,
        TextLoader,
        DirectoryLoader
    )
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_chroma import Chroma
    from langchain_huggingface import HuggingFaceEmbeddings
    
    print(f"📂 Loading documents from {docs_dir}...")
    
    docs_path = Path(docs_dir)
    if not docs_path.exists():
        docs_path.mkdir(parents=True, exist_ok=True)
        print(f"⚠️ Created empty docs directory. Add documents and re-run.")
        return
    
    # Load different document types
    all_docs = []
    
    # PDF files
    pdf_files = list(docs_path.glob("**/*.pdf"))
    for pdf_file in pdf_files:
        try:
            loader = PyPDFLoader(str(pdf_file))
            docs = loader.load()
            for doc in docs:
                doc.metadata["source"] = pdf_file.name
                doc.metadata["doc_type"] = categorize_doc(pdf_file.name)
            all_docs.extend(docs)
            print(f"  ✓ Loaded {pdf_file.name} ({len(docs)} pages)")
        except Exception as e:
            print(f"  ✗ Error loading {pdf_file.name}: {e}")
    
    # Text files
    txt_files = list(docs_path.glob("**/*.txt"))
    for txt_file in txt_files:
        try:
            loader = TextLoader(str(txt_file), encoding="utf-8")
            docs = loader.load()
            for doc in docs:
                doc.metadata["source"] = txt_file.name
                doc.metadata["doc_type"] = categorize_doc(txt_file.name)
            all_docs.extend(docs)
            print(f"  ✓ Loaded {txt_file.name}")
        except Exception as e:
            print(f"  ✗ Error loading {txt_file.name}: {e}")
    
    if not all_docs:
        print("⚠️ No documents found. Creating demo documents...")
        all_docs = create_demo_documents()
    
    print(f"\n📄 Total documents loaded: {len(all_docs)}")
    
    # Chunking
    print(f"\n✂️ Splitting into chunks (size={chunk_size}, overlap={chunk_overlap})...")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n## ", "\n### ", "\n\n", "\n", ". ", " "],
        length_function=len
    )
    
    chunks = splitter.split_documents(all_docs)
    
    # Enrich metadata
    for i, chunk in enumerate(chunks):
        chunk.metadata["chunk_id"] = i
        chunk.metadata["timestamp_indexed"] = datetime.now().isoformat()
    
    print(f"📦 Created {len(chunks)} chunks")
    
    # Build vector store
    print(f"\n🧮 Building embeddings and vector store...")
    print("   Using HuggingFace embeddings (free, local)")
    
    # Use free HuggingFace embeddings (no API key needed)
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )
    
    # Create persist directory
    Path(persist_dir).mkdir(parents=True, exist_ok=True)
    
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=persist_dir
    )
    
    print(f"✅ Vector store built and persisted to {persist_dir}")
    print(f"   - {len(chunks)} chunks indexed")
    
    return vectorstore


def load_vectorstore(persist_dir: str = "data/vectorstore"):
    """
    Load an existing vector store from disk.
    
    Args:
        persist_dir: Directory where the vector store is persisted
        
    Returns:
        ChromaDB vector store or None if not found
    """
    from langchain_chroma import Chroma
    from langchain_huggingface import HuggingFaceEmbeddings
    
    persist_path = Path(persist_dir)
    if not persist_path.exists():
        print(f"⚠️ Vector store not found at {persist_dir}")
        return None
    
    # Use free HuggingFace embeddings (no API key needed)
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )
    
    vectorstore = Chroma(
        persist_directory=persist_dir,
        embedding_function=embeddings
    )
    
    return vectorstore


def categorize_doc(filename: str) -> str:
    """Categorize document type based on filename."""
    filename_lower = filename.lower()
    
    if any(word in filename_lower for word in ["procedure", "proc", "instruction"]):
        return "procedure"
    elif any(word in filename_lower for word in ["rapport", "report", "compte-rendu"]):
        return "rapport"
    elif any(word in filename_lower for word in ["spec", "specification", "technique"]):
        return "specification"
    elif any(word in filename_lower for word in ["safety", "securite", "sûreté"]):
        return "safety"
    elif any(word in filename_lower for word in ["maintenance", "entretien"]):
        return "maintenance"
    else:
        return "document"


def create_demo_documents():
    """Create demo documents for testing without real PDFs."""
    from langchain.schema import Document
    
    demo_docs = [
        Document(
            page_content="""
# Procédure de Maintenance Préventive des Pompes Primaires

## 1. Objectif
Cette procédure définit les étapes de maintenance préventive des pompes du circuit primaire.

## 2. Fréquence
- Inspection visuelle: Mensuelle
- Maintenance complète: Annuelle
- Remplacement joints: Tous les 3 ans

## 3. Étapes
1. Isoler la pompe du circuit
2. Vidanger le fluide caloporteur
3. Démonter le carter de protection
4. Inspecter les paliers et roulements
5. Vérifier l'alignement de l'arbre
6. Remplacer les joints si nécessaire
7. Remonter et tester

## 4. Critères d'acceptation
- Vibrations < 2.5 mm/s
- Température paliers < 80°C
- Débit nominal ± 5%
            """,
            metadata={"source": "PROC-PUMP-001.pdf", "page": 1, "doc_type": "procedure"}
        ),
        Document(
            page_content="""
# Rapport d'Inspection Semestrielle - Réacteur PWR

## Résumé Exécutif
L'inspection du 15 janvier 2025 a confirmé le bon état général des équipements.
Aucune anomalie majeure détectée.

## Points d'attention
1. Usure légère sur vanne V-102 (à surveiller)
2. Traces de corrosion sur tuyauterie secondaire (traitement prévu)

## Métriques clés
- Disponibilité: 98.5%
- Temps moyen entre pannes (MTBF): 2500h
- Incidents niveau 0: 3
- Incidents niveau 1: 0

## Recommandations
- Planifier remplacement vanne V-102 lors du prochain arrêt
- Renforcer programme anti-corrosion
            """,
            metadata={"source": "RAPPORT-INSP-2025-001.pdf", "page": 1, "doc_type": "rapport"}
        ),
        Document(
            page_content="""
# Spécification Technique - Capteurs de Température

## 1. Généralités
Les capteurs de température du circuit primaire sont de type PT100 classe A.

## 2. Caractéristiques
- Plage de mesure: 0-400°C
- Précision: ±0.15°C
- Temps de réponse: < 5s
- Résistance à la pression: 160 bar

## 3. Étalonnage
L'étalonnage doit être effectué annuellement selon la procédure PROC-CAL-001.
Points de calibration: 0°C, 100°C, 200°C, 300°C

## 4. Remplacement
Durée de vie nominale: 10 ans
Critères de remplacement:
- Dérive > 0.5°C
- Temps de réponse > 10s
- Dommage physique visible
            """,
            metadata={"source": "SPEC-TEMP-SENSORS.pdf", "page": 1, "doc_type": "specification"}
        ),
        Document(
            page_content="""
# Guide de Sûreté Nucléaire - Principes Fondamentaux

## Défense en Profondeur
Le concept de défense en profondeur repose sur plusieurs barrières successives:

1. **Première barrière**: Gaine du combustible
2. **Deuxième barrière**: Enveloppe du circuit primaire
3. **Troisième barrière**: Enceinte de confinement

## Critères de Sûreté
- Contrôle de la réactivité
- Évacuation de la chaleur résiduelle
- Confinement des matières radioactives

## Niveaux INES
- Niveau 0: Écart (pas d'impact sur la sûreté)
- Niveau 1: Anomalie
- Niveau 2: Incident
- Niveau 3: Incident grave
- Niveau 4-7: Accident
            """,
            metadata={"source": "GUIDE-SURETE-001.pdf", "page": 1, "doc_type": "safety"}
        ),
    ]
    
    return demo_docs


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Build vector store from documents")
    parser.add_argument("--docs-dir", default="data/docs", help="Documents directory")
    parser.add_argument("--persist-dir", default="data/vectorstore", help="Output directory")
    parser.add_argument("--chunk-size", type=int, default=800, help="Chunk size")
    parser.add_argument("--chunk-overlap", type=int, default=150, help="Chunk overlap")
    
    args = parser.parse_args()
    
    build_vectorstore(
        docs_dir=args.docs_dir,
        persist_dir=args.persist_dir,
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap
    )
