"""
LLM Configuration - Centralized LLM provider setup

Supports:
- Groq (default, free tier available)
- OpenAI (fallback)
"""

import os
import streamlit as st
from typing import Optional


def get_llm(temperature: float = 0.1):
    """
    Get configured LLM instance.
    
    Priority:
    1. Groq (if GROQ_API_KEY configured)
    2. OpenAI (fallback)
    
    Args:
        temperature: LLM temperature setting
        
    Returns:
        LangChain chat model instance
    """
    # Try Groq first (free and fast)
    groq_key = _get_api_key("groq")
    if groq_key:
        from langchain_groq import ChatGroq
        return ChatGroq(
            model="llama-3.3-70b-versatile",  # or "mixtral-8x7b-32768"
            temperature=temperature,
            api_key=groq_key
        )
    
    # Fallback to OpenAI
    openai_key = _get_api_key("openai")
    if openai_key:
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model="gpt-4o-mini",
            temperature=temperature,
            api_key=openai_key
        )
    
    raise ValueError(
        "No API key found. Please configure either:\n"
        "- [groq] api_key in .streamlit/secrets.toml\n"
        "- [openai] api_key in .streamlit/secrets.toml\n"
        "Or set GROQ_API_KEY or OPENAI_API_KEY environment variable."
    )


def get_embeddings():
    """
    Get embeddings model.
    
    Priority:
    1. Local HuggingFace (free, no API needed)
    2. OpenAI embeddings (if key available)
    
    Returns:
        LangChain embeddings instance
    """
    # Try local embeddings first (free, no API key needed)
    try:
        from langchain_huggingface import HuggingFaceEmbeddings
        return HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
    except Exception as e:
        print(f"⚠️ Could not load local embeddings: {e}")
    
    # Fallback to OpenAI
    openai_key = _get_api_key("openai")
    if openai_key:
        from langchain_openai import OpenAIEmbeddings
        return OpenAIEmbeddings(
            model="text-embedding-3-small",
            api_key=openai_key
        )
    
    raise ValueError(
        "No embeddings available. Install sentence-transformers or configure OpenAI API key."
    )


def _get_api_key(provider: str) -> Optional[str]:
    """Get API key from Streamlit secrets or environment."""
    # Try Streamlit secrets
    try:
        key = st.secrets.get(provider, {}).get("api_key")
        if key:
            return key
    except Exception:
        pass
    
    # Try environment variable
    env_var = f"{provider.upper()}_API_KEY"
    return os.getenv(env_var)


def get_provider_info() -> dict:
    """Get information about configured providers."""
    info = {
        "groq": bool(_get_api_key("groq")),
        "openai": bool(_get_api_key("openai")),
        "embeddings": "unknown"
    }
    
    try:
        emb = get_embeddings()
        info["embeddings"] = type(emb).__name__
    except Exception:
        info["embeddings"] = "none"
    
    return info
