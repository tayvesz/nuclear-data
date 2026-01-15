"""
Summary Agent (SummaryAgent) - Multi-Source Synthesis

Specializes in:
- Aggregating results from multiple agents
- Generating executive summaries
- Structuring actionable responses
- Cross-referencing documentation with data
"""

from typing import Dict, Any, List
from langchain_core.messages import HumanMessage, SystemMessage
import streamlit as st

# Import centralized LLM config
from .llm_config import get_llm


SUMMARY_AGENT_SYSTEM_PROMPT = """Tu es l'assistant IA de Framatome (Nucléaire AI).

Ton rôle est de répondre à l'utilisateur de manière NATURELLE, DIRECTE et PRÉCISE.

RÈGLES D'OR :
1. **Réponse directe d'abord** : Commence immédiatement par la réponse (le chiffre, le fait, ou l'explication).
   - "Il y a 56 réacteurs opérationnels en France." (OUI)
   - "Résumé exécutif : Le parc compte..." (NON)
2. **Pas de structure rigide** : N'utilise pas de titres comme "Résumé exécutif" ou "Points principaux" sauf si la réponse le nécessite vraiment (très longue).
3. **Concision** : Sois bref. L'utilisateur veut l'info, pas un discours.
4. **Contexte** : Utilise le SQL ou les docs fournis pour justifier ta réponse si besoin, mais sans te répéter.

Si la réponse est un simple chiffre (ex: "56"), donne le chiffre et une phrase de contexte courte. C'est tout.
"""




def aggregate_results(doc_results: Dict, data_results: Dict) -> str:
    """
    Aggregate results from DocAgent and DataAgent.
    
    Returns formatted context for synthesis.
    """
    context_parts = []
    
    # Document results
    if doc_results and doc_results.get("answer"):
        context_parts.append(f"""
## Résultats documentaires (DocAgent)
{doc_results['answer']}
""")
    
    # Data results
    if data_results and data_results.get("success"):
        data_summary = f"""
## Résultats analytiques (DataAgent)
- Nombre de lignes: {data_results.get('row_count', 'N/A')}
- Colonnes: {', '.join(data_results.get('columns', []))}
"""
        if data_results.get("statistics"):
            data_summary += "\n**Statistiques:**\n"
            for col, stats in data_results["statistics"].items():
                if "mean" in stats:
                    data_summary += f"- {col}: moyenne={stats['mean']:.2f}, écart-type={stats['std']:.2f}\n"
                elif "top_values" in stats:
                    top = list(stats["top_values"].items())[:3]
                    data_summary += f"- {col}: {top}\n"
        
        context_parts.append(data_summary)
    elif data_results and data_results.get("error"):
        context_parts.append(f"""
## Résultats analytiques (DataAgent)
⚠️ Erreur: {data_results['error']}
""")
    
    if not context_parts:
        return "Aucun résultat disponible des autres agents."
    
    return "\n".join(context_parts)


def generate_executive_summary(context: str, question: str) -> str:
    """
    Generate an executive summary from aggregated results.
    """
    llm = get_llm()
    
    prompt = f"""Génère une synthèse exécutive basée sur ces résultats.

QUESTION ORIGINALE: {question}

RÉSULTATS DES AGENTS:
{context}

Fournis une réponse structurée avec:
1. Résumé exécutif (2-3 phrases)
2. Points clés numérotés
3. Données chiffrées si disponibles
4. Recommandations si pertinent

Utilise le format Markdown pour la structure."""
    
    response = llm.invoke([
        SystemMessage(content=SUMMARY_AGENT_SYSTEM_PROMPT),
        HumanMessage(content=prompt)
    ])
    
    return response.content


def summary_agent_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Summary agent node.
    
    Synthesizes results from DocAgent and DataAgent into
    a coherent, actionable response.
    """
    question = state["messages"][0] if state["messages"] else ""  # Original question
    doc_results = state.get("doc_results", {})
    data_results = state.get("data_results", {})
    
    # Check if we have any results to synthesize
    has_doc = bool(doc_results and doc_results.get("answer"))
    has_data = bool(data_results and (data_results.get("success") or data_results.get("error")))
    
    if not has_doc and not has_data:
        # No prior results - this was routed directly to SummaryAgent
        # Generate a general synthesis response
        llm = get_llm()
        
        prompt = f"""Question: {question}

Cette question semble nécessiter une analyse multi-facettes. 
Fournis une réponse générale structurée qui couvre les différents aspects de la question.
Si des données spécifiques seraient nécessaires, indique-le.

Utilise le format Markdown."""
        
        response = llm.invoke([
            SystemMessage(content=SUMMARY_AGENT_SYSTEM_PROMPT),
            HumanMessage(content=prompt)
        ])
        
        answer = response.content
    else:
        # Aggregate results from other agents
        context = aggregate_results(doc_results, data_results)
        
        # Generate executive summary
        try:
            answer = generate_executive_summary(context, question)
            
            # Append sources if available
            if doc_results.get("sources"):
                answer += "\n\n---\n📚 **Sources documentaires:**\n"
                for src in doc_results["sources"][:3]:
                    source = src.get("metadata", {}).get("source", "N/A")
                    page = src.get("metadata", {}).get("page", "N/A")
                    score = src.get("score", 0)
                    answer += f"- {source} (p.{page}) - pertinence: {1-score:.1%}\n"
            
            if data_results.get("sql"):
                answer += f"\n\n📊 **Requête SQL utilisée:**\n```sql\n{data_results['sql']}\n```"
                
        except Exception as e:
            answer = f"❌ Erreur lors de la synthèse: {str(e)}"
    
    return {
        "final_answer": answer,
        "messages": [f"[SummaryAgent] {answer}"]
    }
