"""
Visualization Agent (VizAgent) - Plotly Chart Generation

Specializes in:
- Intelligent chart type selection
- Secure Plotly visualization generation
- Column validation with fuzzy matching
- Reproducible Python code generation
"""

from typing import Dict, Any, List, Optional
from langchain_core.messages import HumanMessage, SystemMessage
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import streamlit as st
from thefuzz import process as fuzzy_process
import json

# Import centralized LLM config
from .llm_config import get_llm


VIZ_AGENT_SYSTEM_PROMPT = """Tu es un expert en visualisation de données industrielles pour Framatome.

TYPES DE GRAPHIQUES DISPONIBLES:
- bar: Comparaisons entre catégories
- line: Évolutions temporelles
- scatter: Corrélations entre variables
- box: Distribution statistique
- pie: Répartitions en pourcentage
- histogram: Distribution d'une variable
- heatmap: Matrices de corrélation

INSTRUCTIONS:
1. Analyse la demande et les données disponibles
2. Choisis le type de graphique le plus adapté
3. Valide que les colonnes existent dans le DataFrame
4. Génère un graphique clair avec titre et labels appropriés
5. Retourne le code Python pour reproductibilité

BONNES PRATIQUES:
- Titres explicites et professionnels
- Labels d'axes avec unités si applicable
- Couleurs cohérentes avec le thème industriel
- Légendes claires pour les séries multiples
"""




def get_available_dataframe() -> Optional[pd.DataFrame]:
    """Get the most recent DataFrame from session state."""
    # Try last query result first
    df = st.session_state.get("last_query_df")
    if df is not None and len(df) > 0:
        return df
    
    # Try operational data
    df = st.session_state.get("operational_data")
    if df is not None:
        return df
    
    return None


def validate_column(column: str, df: pd.DataFrame) -> tuple[str, bool]:
    """
    Validate column name with fuzzy matching.
    
    Returns:
        Tuple of (matched_column, is_exact_match)
    """
    if column in df.columns:
        return column, True
    
    # Fuzzy match
    matches = fuzzy_process.extractBests(column, df.columns, score_cutoff=60, limit=3)
    if matches:
        return matches[0][0], False
    
    return column, False


def suggest_viz_type(df: pd.DataFrame, question: str) -> Dict[str, Any]:
    """
    Suggest the best visualization type based on data and question.
    
    Returns:
        Dict with chart_type, x_col, y_col, color, suggestions
    """
    llm = get_llm()
    
    # Get column info
    columns_info = []
    for col in df.columns:
        dtype = str(df[col].dtype)
        unique = df[col].nunique()
        columns_info.append(f"- {col}: {dtype} ({unique} valeurs uniques)")
    
    columns_str = "\n".join(columns_info)
    sample = df.head(3).to_markdown(index=False)
    
    prompt = f"""Analyse ces données et la question pour suggérer une visualisation.

COLONNES DISPONIBLES:
{columns_str}

ÉCHANTILLON:
{sample}

QUESTION: {question}

Retourne un JSON avec:
{{
    "chart_type": "bar|line|scatter|box|pie|histogram",
    "x_col": "nom_colonne_x",
    "y_col": "nom_colonne_y",
    "color": "nom_colonne_couleur ou null",
    "title": "Titre du graphique",
    "reasoning": "Explication du choix"
}}

IMPORTANT: Les colonnes doivent exister dans les données.
JSON:"""
    
    response = llm.invoke([HumanMessage(content=prompt)])
    content = response.content.strip()
    
    # Parse JSON
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
    content = content.strip()
    
    try:
        config = json.loads(content)
    except json.JSONDecodeError:
        # Default config
        config = {
            "chart_type": "bar",
            "x_col": df.columns[0],
            "y_col": df.columns[1] if len(df.columns) > 1 else df.columns[0],
            "color": None,
            "title": "Visualisation des données",
            "reasoning": "Configuration par défaut"
        }
    
    return config


def generate_chart(
    df: pd.DataFrame,
    chart_type: str,
    x_col: str,
    y_col: str,
    title: str,
    color: Optional[str] = None
) -> tuple[Optional[go.Figure], str]:
    """
    Generate a Plotly chart from validated configuration.
    
    Returns:
        Tuple of (figure, python_code)
    """
    # Validate columns
    x_col_valid, x_exact = validate_column(x_col, df)
    y_col_valid, y_exact = validate_column(y_col, df)
    
    if x_col_valid not in df.columns:
        return None, f"Colonne X '{x_col}' non trouvée. Colonnes disponibles: {list(df.columns)}"
    if y_col_valid not in df.columns:
        return None, f"Colonne Y '{y_col}' non trouvée. Colonnes disponibles: {list(df.columns)}"
    
    color_valid = None
    if color:
        color_valid, _ = validate_column(color, df)
        if color_valid not in df.columns:
            color_valid = None
    
    # Update column names if fuzzy matched
    x_col = x_col_valid
    y_col = y_col_valid
    color = color_valid
    
    # Chart generation templates
    try:
        chart_funcs = {
            "bar": lambda: px.bar(df, x=x_col, y=y_col, color=color, title=title,
                                  color_discrete_sequence=px.colors.qualitative.Set2),
            "line": lambda: px.line(df, x=x_col, y=y_col, color=color, title=title,
                                    color_discrete_sequence=px.colors.qualitative.Set2),
            "scatter": lambda: px.scatter(df, x=x_col, y=y_col, color=color, title=title,
                                          color_discrete_sequence=px.colors.qualitative.Set2),
            "box": lambda: px.box(df, x=x_col, y=y_col, color=color, title=title,
                                  color_discrete_sequence=px.colors.qualitative.Set2),
            "pie": lambda: px.pie(df, values=y_col, names=x_col, title=title,
                                  color_discrete_sequence=px.colors.qualitative.Set2),
            "histogram": lambda: px.histogram(df, x=x_col, color=color, title=title,
                                              color_discrete_sequence=px.colors.qualitative.Set2),
        }
        
        if chart_type not in chart_funcs:
            chart_type = "bar"
        
        fig = chart_funcs[chart_type]()
        
        # Apply consistent styling
        fig.update_layout(
            template="plotly_dark",
            font=dict(family="Arial, sans-serif", size=12),
            title_font_size=16,
            legend_title_font_size=12,
            hoverlabel=dict(font_size=12),
            margin=dict(l=60, r=40, t=60, b=60)
        )
        
        # Generate reproducible code
        color_str = f"color='{color}', " if color else ""
        code = f"""import plotly.express as px

# Charger vos données dans df

fig = px.{chart_type}(
    df, 
    x='{x_col}', 
    y='{y_col}', 
    {color_str}title='{title}',
    color_discrete_sequence=px.colors.qualitative.Set2
)

fig.update_layout(template='plotly_dark')
fig.show()
"""
        
        return fig, code
        
    except Exception as e:
        return None, f"Erreur génération graphique: {str(e)}"


def viz_agent_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Visualization agent node.
    
    Analyzes request, validates data, and generates Plotly charts.
    """
    question = state["messages"][-1] if state["messages"] else ""
    
    # Get available DataFrame
    df = get_available_dataframe()
    
    if df is None or len(df) == 0:
        return {
            "viz_results": {
                "success": False,
                "error": "Aucune donnée disponible pour la visualisation. Exécutez d'abord une requête de données."
            },
            "messages": ["[VizAgent] ❌ Aucune donnée disponible"],
            "final_answer": "❌ Aucune donnée disponible pour créer une visualisation. Veuillez d'abord interroger les données."
        }
    
    try:
        # Get visualization suggestion from LLM
        config = suggest_viz_type(df, question)
        
        # Generate the chart
        fig, code = generate_chart(
            df=df,
            chart_type=config.get("chart_type", "bar"),
            x_col=config.get("x_col", df.columns[0]),
            y_col=config.get("y_col", df.columns[-1]),
            title=config.get("title", "Visualisation"),
            color=config.get("color")
        )
        
        if fig is None:
            # Code contains error message
            return {
                "viz_results": {
                    "success": False,
                    "error": code,
                    "config": config
                },
                "messages": [f"[VizAgent] ❌ {code}"],
                "final_answer": f"❌ {code}"
            }
        
        # Success response
        reasoning = config.get("reasoning", "")
        answer = f"""📊 **Graphique généré avec succès !**

**Type:** {config.get('chart_type', 'bar').capitalize()}
**Raison:** {reasoning}

Le graphique est affiché ci-dessous."""
        
        return {
            "viz_results": {
                "success": True,
                "figure": fig,
                "code": code,
                "config": config
            },
            "messages": [f"[VizAgent] {answer}"],
            "final_answer": answer
        }
        
    except Exception as e:
        return {
            "viz_results": {
                "success": False,
                "error": str(e)
            },
            "messages": [f"[VizAgent] ❌ Erreur: {str(e)}"],
            "final_answer": f"❌ Erreur lors de la création du graphique: {str(e)}"
        }
