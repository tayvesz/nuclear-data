"""
Data Tools - SQL and Statistics Operations

Tools for querying operational databases and computing statistics.
"""

from typing import Dict, Any, List, Optional
from langchain.tools import tool
import pandas as pd
import sqlite3
import streamlit as st
import numpy as np


def get_db_connection(db_path: Optional[str] = None):
    """Get SQLite database connection."""
    if db_path is None:
        db_path = st.session_state.get("db_path", "data/operational.db")
    return sqlite3.connect(db_path)


@tool
def query_operational_data(sql_query: str) -> Dict[str, Any]:
    """
    Exécute une requête SQL sur la base de données opérationnelle.
    
    Args:
        sql_query: Requête SQL SELECT
        
    Returns:
        Dictionnaire avec les données, métadonnées et statut
    """
    try:
        conn = get_db_connection()
        
        # Security: Only allow SELECT
        sql_upper = sql_query.strip().upper()
        if not sql_upper.startswith("SELECT"):
            return {
                "success": False,
                "error": "Seules les requêtes SELECT sont autorisées",
                "data": None
            }
        
        # Execute query
        df = pd.read_sql_query(sql_query, conn)
        conn.close()
        
        # Limit results
        if len(df) > 100:
            df = df.head(100)
            truncated = True
        else:
            truncated = False
        
        # Store for VizAgent
        st.session_state["last_query_df"] = df
        
        return {
            "success": True,
            "data": df.to_dict(orient="records"),
            "columns": list(df.columns),
            "row_count": len(df),
            "truncated": truncated,
            "sql": sql_query
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "data": None
        }


@tool
def compute_statistics(metric: str, table: str = "maintenances", 
                       group_by: Optional[str] = None) -> Dict[str, Any]:
    """
    Calcule des statistiques sur une métrique.
    
    Args:
        metric: Nom de la colonne numérique à analyser
        table: Nom de la table (maintenances, incidents, reactors)
        group_by: Colonne optionnelle pour grouper les stats
        
    Returns:
        Statistiques descriptives (moyenne, écart-type, min, max, médiane)
    """
    try:
        conn = get_db_connection()
        
        if group_by:
            query = f"SELECT {group_by}, {metric} FROM {table}"
        else:
            query = f"SELECT {metric} FROM {table}"
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        if metric not in df.columns:
            return {
                "success": False,
                "error": f"Colonne '{metric}' non trouvée dans {table}"
            }
        
        if not pd.api.types.is_numeric_dtype(df[metric]):
            return {
                "success": False,
                "error": f"Colonne '{metric}' n'est pas numérique"
            }
        
        if group_by and group_by in df.columns:
            # Grouped statistics
            stats = df.groupby(group_by)[metric].agg([
                'count', 'mean', 'std', 'min', 'max', 'median'
            ]).reset_index()
            
            return {
                "success": True,
                "grouped": True,
                "group_by": group_by,
                "statistics": stats.to_dict(orient="records")
            }
        else:
            # Global statistics
            return {
                "success": True,
                "grouped": False,
                "metric": metric,
                "statistics": {
                    "count": int(df[metric].count()),
                    "mean": float(df[metric].mean()),
                    "std": float(df[metric].std()) if len(df) > 1 else 0.0,
                    "min": float(df[metric].min()),
                    "max": float(df[metric].max()),
                    "median": float(df[metric].median()),
                    "sum": float(df[metric].sum())
                }
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@tool
def count_by_category(dimension: str, table: str = "maintenances",
                      filter_condition: Optional[str] = None) -> Dict[str, Any]:
    """
    Compte les enregistrements par catégorie.
    
    Args:
        dimension: Colonne à utiliser pour le groupement
        table: Nom de la table
        filter_condition: Condition WHERE optionnelle (ex: "status = 'completed'")
        
    Returns:
        Comptages par catégorie
    """
    try:
        conn = get_db_connection()
        
        where_clause = f"WHERE {filter_condition}" if filter_condition else ""
        query = f"""
            SELECT {dimension}, COUNT(*) as count 
            FROM {table} 
            {where_clause}
            GROUP BY {dimension}
            ORDER BY count DESC
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        # Store for potential viz
        st.session_state["last_query_df"] = df
        
        return {
            "success": True,
            "dimension": dimension,
            "table": table,
            "total": int(df['count'].sum()),
            "categories": df.to_dict(orient="records")
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def get_table_info(table: str = None) -> Dict[str, Any]:
    """Get information about database tables."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if table:
            # Info for specific table
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                "table": table,
                "columns": [
                    {"name": col[1], "type": col[2], "nullable": not col[3]}
                    for col in columns
                ],
                "row_count": count
            }
        else:
            # List all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [t[0] for t in cursor.fetchall()]
            
            result = {"tables": []}
            for t in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {t}")
                count = cursor.fetchone()[0]
                result["tables"].append({"name": t, "row_count": count})
            
            conn.close()
            return result
            
    except Exception as e:
        return {"error": str(e)}


def get_date_range(table: str = "maintenances", date_column: str = "date") -> Dict[str, str]:
    """Get the date range for a table."""
    try:
        conn = get_db_connection()
        query = f"SELECT MIN({date_column}) as min_date, MAX({date_column}) as max_date FROM {table}"
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        return {
            "min_date": str(df.iloc[0]["min_date"]),
            "max_date": str(df.iloc[0]["max_date"])
        }
    except Exception:
        return {"min_date": "N/A", "max_date": "N/A"}
