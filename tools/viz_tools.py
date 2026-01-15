"""
Visualization Tools - Plotly Chart Generation

Tools for creating validated, reproducible visualizations.
"""

from typing import Dict, Any, List, Optional, Literal
from langchain.tools import tool
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import streamlit as st
from thefuzz import process as fuzzy_process


# Color palette for industrial/nuclear theme
FRAMATOME_COLORS = [
    "#0066CC",  # Primary blue
    "#FF6B35",  # Safety orange
    "#2ECC71",  # Success green
    "#9B59B6",  # Purple
    "#E74C3C",  # Alert red
    "#3498DB",  # Light blue
    "#1ABC9C",  # Teal
    "#F39C12",  # Warning yellow
]


def validate_columns(columns: List[str], df: pd.DataFrame) -> Dict[str, str]:
    """
    Validate and fuzzy-match column names.
    
    Returns:
        Dict mapping requested columns to actual columns
    """
    mapping = {}
    for col in columns:
        if col in df.columns:
            mapping[col] = col
        else:
            matches = fuzzy_process.extractBests(col, df.columns, score_cutoff=60, limit=1)
            if matches:
                mapping[col] = matches[0][0]
            else:
                mapping[col] = None
    return mapping


@tool
def suggest_viz_type(data_summary: str) -> Dict[str, Any]:
    """
    Recommande le type de graphique basé sur les données.
    
    Args:
        data_summary: Description des données disponibles (colonnes, types, tailles)
        
    Returns:
        Recommandation avec type de graphique et configuration suggérée
    """
    # Heuristics for chart type selection
    summary_lower = data_summary.lower()
    
    recommendations = []
    
    # Time series detection
    if any(word in summary_lower for word in ["date", "time", "année", "mois", "jour", "temporal"]):
        recommendations.append({
            "type": "line",
            "reason": "Données temporelles détectées - graphique linéaire recommandé pour voir l'évolution",
            "priority": 1
        })
    
    # Categorical comparison
    if any(word in summary_lower for word in ["catégorie", "type", "status", "category", "groupe"]):
        recommendations.append({
            "type": "bar",
            "reason": "Données catégorielles - histogramme pour comparer les catégories",
            "priority": 2
        })
    
    # Distribution analysis
    if any(word in summary_lower for word in ["distribution", "répartition", "spread", "variance"]):
        recommendations.append({
            "type": "box",
            "reason": "Analyse de distribution - box plot pour voir les quartiles",
            "priority": 3
        })
    
    # Correlation
    if any(word in summary_lower for word in ["corrélation", "relation", "scatter", "nuage"]):
        recommendations.append({
            "type": "scatter",
            "reason": "Relation entre variables - nuage de points recommandé",
            "priority": 2
        })
    
    # Proportion
    if any(word in summary_lower for word in ["pourcentage", "proportion", "part", "%", "pie"]):
        recommendations.append({
            "type": "pie",
            "reason": "Répartition en proportions - diagramme circulaire",
            "priority": 3
        })
    
    # Default
    if not recommendations:
        recommendations.append({
            "type": "bar",
            "reason": "Type par défaut - histogramme polyvalent",
            "priority": 5
        })
    
    # Sort by priority
    recommendations.sort(key=lambda x: x["priority"])
    
    return {
        "primary_recommendation": recommendations[0],
        "alternatives": recommendations[1:3] if len(recommendations) > 1 else [],
        "available_types": ["bar", "line", "scatter", "box", "pie", "histogram", "heatmap"]
    }


@tool
def generate_plotly_chart(
    chart_type: Literal["bar", "line", "scatter", "box", "pie", "histogram"],
    x_col: str,
    y_col: str,
    title: str,
    color_col: Optional[str] = None,
    aggregation: Optional[str] = None
) -> Dict[str, Any]:
    """
    Génère un graphique Plotly validé à partir d'une configuration.
    
    Args:
        chart_type: Type de graphique (bar, line, scatter, box, pie, histogram)
        x_col: Nom de la colonne pour l'axe X
        y_col: Nom de la colonne pour l'axe Y
        title: Titre du graphique
        color_col: Colonne optionnelle pour la couleur/groupement
        aggregation: Agrégation optionnelle (sum, mean, count)
        
    Returns:
        Dictionnaire avec figure Plotly, code Python, et métadonnées
    """
    # Get DataFrame from session
    df = st.session_state.get("last_query_df")
    
    if df is None or len(df) == 0:
        return {
            "success": False,
            "error": "Aucune donnée disponible. Exécutez d'abord une requête.",
            "figure": None,
            "code": None
        }
    
    # Validate columns
    cols_to_check = [x_col, y_col]
    if color_col:
        cols_to_check.append(color_col)
    
    col_mapping = validate_columns(cols_to_check, df)
    
    # Check for invalid columns
    invalid_cols = [c for c, mapped in col_mapping.items() if mapped is None]
    if invalid_cols:
        suggestions = {c: list(fuzzy_process.extractBests(c, df.columns, limit=3)) 
                      for c in invalid_cols}
        return {
            "success": False,
            "error": f"Colonnes non trouvées: {invalid_cols}",
            "suggestions": suggestions,
            "available_columns": list(df.columns),
            "figure": None,
            "code": None
        }
    
    # Map to actual columns
    x_col = col_mapping[x_col]
    y_col = col_mapping[y_col]
    color_col = col_mapping.get(color_col) if color_col else None
    
    # Apply aggregation if requested
    if aggregation and aggregation in ["sum", "mean", "count"]:
        if aggregation == "count":
            df = df.groupby(x_col).size().reset_index(name=y_col)
        else:
            df = df.groupby(x_col)[y_col].agg(aggregation).reset_index()
    
    try:
        # Chart generation
        chart_configs = {
            "bar": lambda: px.bar(
                df, x=x_col, y=y_col, color=color_col, 
                title=title, color_discrete_sequence=FRAMATOME_COLORS
            ),
            "line": lambda: px.line(
                df, x=x_col, y=y_col, color=color_col,
                title=title, color_discrete_sequence=FRAMATOME_COLORS
            ),
            "scatter": lambda: px.scatter(
                df, x=x_col, y=y_col, color=color_col,
                title=title, color_discrete_sequence=FRAMATOME_COLORS
            ),
            "box": lambda: px.box(
                df, x=x_col, y=y_col, color=color_col,
                title=title, color_discrete_sequence=FRAMATOME_COLORS
            ),
            "pie": lambda: px.pie(
                df, values=y_col, names=x_col,
                title=title, color_discrete_sequence=FRAMATOME_COLORS
            ),
            "histogram": lambda: px.histogram(
                df, x=x_col, color=color_col,
                title=title, color_discrete_sequence=FRAMATOME_COLORS
            ),
        }
        
        fig = chart_configs[chart_type]()
        
        # Apply consistent styling
        fig.update_layout(
            template="plotly_dark",
            font=dict(family="Arial, sans-serif", size=12, color="#FAFAFA"),
            title_font=dict(size=16, color="#FAFAFA"),
            paper_bgcolor="#0E1117",
            plot_bgcolor="#262730",
            legend=dict(
                bgcolor="rgba(0,0,0,0.5)",
                bordercolor="#444",
                borderwidth=1
            ),
            margin=dict(l=60, r=40, t=60, b=60),
            hoverlabel=dict(
                bgcolor="#333",
                font_size=12,
                font_family="Arial"
            )
        )
        
        # Generate reproducible Python code
        color_param = f", color='{color_col}'" if color_col else ""
        code = f'''import plotly.express as px
import pandas as pd

# Charger vos données
# df = pd.read_sql("votre_requete", connection)

# Palette Framatome
FRAMATOME_COLORS = {FRAMATOME_COLORS}

fig = px.{chart_type}(
    df,
    x='{x_col}',
    y='{y_col}'{color_param},
    title='{title}',
    color_discrete_sequence=FRAMATOME_COLORS
)

fig.update_layout(
    template='plotly_dark',
    paper_bgcolor='#0E1117',
    plot_bgcolor='#262730'
)

fig.show()
'''
        
        return {
            "success": True,
            "figure": fig,
            "code": code,
            "config": {
                "chart_type": chart_type,
                "x_col": x_col,
                "y_col": y_col,
                "color_col": color_col,
                "title": title,
                "data_points": len(df)
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Erreur de génération: {str(e)}",
            "figure": None,
            "code": None
        }


def create_quick_chart(df: pd.DataFrame, chart_type: str = "bar") -> go.Figure:
    """
    Create a quick chart from a DataFrame with automatic column detection.
    """
    if len(df.columns) < 2:
        # Single column - histogram
        fig = px.histogram(df, x=df.columns[0], color_discrete_sequence=FRAMATOME_COLORS)
    else:
        # Use first categorical/string column for X, first numeric for Y
        x_col = None
        y_col = None
        
        for col in df.columns:
            if x_col is None and not pd.api.types.is_numeric_dtype(df[col]):
                x_col = col
            if y_col is None and pd.api.types.is_numeric_dtype(df[col]):
                y_col = col
        
        # Fallback
        if x_col is None:
            x_col = df.columns[0]
        if y_col is None:
            y_col = df.columns[1] if len(df.columns) > 1 else df.columns[0]
        
        chart_func = getattr(px, chart_type, px.bar)
        fig = chart_func(df, x=x_col, y=y_col, color_discrete_sequence=FRAMATOME_COLORS)
    
    fig.update_layout(template="plotly_dark")
    return fig
