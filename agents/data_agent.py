"""
Data Agent (DataAgent) - SQL/Statistics Analysis

Specializes in:
- Querying operational databases
- Computing statistics and metrics
- Trend analysis
- Data aggregation
"""

from typing import Dict, Any, List, Optional
from langchain_core.messages import HumanMessage, SystemMessage
import pandas as pd
import sqlite3
import streamlit as st
import json

# Import centralized LLM config
from .llm_config import get_llm


DATA_AGENT_SYSTEM_PROMPT = """Tu es un analyste de données industriel expert pour Framatome.

Ton rôle est d'interroger les bases de données opérationnelles et fournir des analyses chiffrées précises.

TABLES DISPONIBLES:
1. **reactors** - Données des réacteurs nucléaires mondiaux
   - name, reactor_model, reactor_type, status
   - construction_start_at, operational_from, operational_to
   - thermal_capacity, gross_capacity, country

2. **maintenances** - Historique des maintenances
   - id, reactor_name, equipment, type (préventive/corrective/inspection)
   - date, duration_hours, status (completed/pending)

3. **incidents** - Registre des incidents
   - id, reactor_name, severity (low/medium/high)
   - category (mécanique/électrique/instrumentation/thermique)
   - date, resolved (True/False)

INSTRUCTIONS:
1. Génère des requêtes SQL valides pour SQLite
2. Fournis des chiffres précis avec unités
3. Calcule les statistiques demandées (moyenne, écart-type, etc.)
4. Présente les résultats de manière claire et structurée
5. Ajoute un contexte d'interprétation métier

FORMAT SQL:
- Utilise des noms de colonnes exacts
- Gère les dates au format 'YYYY-MM-DD'
- Limite les résultats à 100 lignes max
"""




def get_db_connection():
    """Get SQLite database connection."""
    db_path = st.session_state.get("db_path", "data/operational.db")
    return sqlite3.connect(db_path)


def get_table_schemas() -> str:
    """Get schema information for all tables."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Get table names
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        schema_info = []
        for table in tables:
            table_name = table[0]
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = cursor.fetchall()
            cols = ", ".join([f"{col[1]} ({col[2]})" for col in columns])
            
            # Get row count
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            
            schema_info.append(f"- {table_name} ({count} lignes): {cols}")
        
        conn.close()
        return "\n".join(schema_info)
        
    except Exception as e:
        return f"Erreur schéma: {str(e)}"


def execute_query(sql: str) -> tuple[Optional[pd.DataFrame], Optional[str]]:
    """
    Execute a SQL query and return results as DataFrame.
    
    Returns:
        Tuple of (DataFrame, error_message)
    """
    try:
        conn = get_db_connection()
        
        # Safety check - only allow SELECT queries
        sql_upper = sql.strip().upper()
        if not sql_upper.startswith("SELECT"):
            return None, "Seules les requêtes SELECT sont autorisées."
        
        # Prevent dangerous operations
        forbidden = ["DROP", "DELETE", "INSERT", "UPDATE", "ALTER", "CREATE", "EXEC"]
        for word in forbidden:
            if word in sql_upper:
                return None, f"Opération interdite: {word}"
        
        # Execute query
        df = pd.read_sql_query(sql, conn)
        conn.close()
        
        # Limit results
        if len(df) > 100:
            df = df.head(100)
        
        return df, None
        
    except Exception as e:
        return None, str(e)


def compute_statistics(df: pd.DataFrame, column: str) -> Dict[str, Any]:
    """Compute descriptive statistics for a column."""
    if column not in df.columns:
        return {"error": f"Colonne {column} non trouvée"}
    
    if pd.api.types.is_numeric_dtype(df[column]):
        return {
            "count": int(df[column].count()),
            "mean": float(df[column].mean()),
            "std": float(df[column].std()),
            "min": float(df[column].min()),
            "max": float(df[column].max()),
            "median": float(df[column].median())
        }
    else:
        return {
            "count": int(df[column].count()),
            "unique": int(df[column].nunique()),
            "top_values": df[column].value_counts().head(5).to_dict()
        }


def generate_sql_query(question: str, schema: str) -> str:
    """Use LLM to generate SQL query from natural language."""
    llm = get_llm()
    
    prompt = f"""Génère une requête SQL SQLite pour répondre à cette question.

SCHÉMA DE LA BASE:
{schema}

QUESTION: {question}

RÈGLES:
- Retourne UNIQUEMENT la requête SQL, sans explication
- Utilise des alias pour les noms de colonnes clairs
- Limite à 100 résultats max
- Utilise strftime pour les dates si nécessaire
- Pour compter par catégorie, utilise GROUP BY

REQUÊTE SQL:"""
    
    response = llm.invoke([HumanMessage(content=prompt)])
    sql = response.content.strip()
    
    # Clean up the SQL (remove markdown code blocks if present)
    if sql.startswith("```"):
        sql = sql.split("```")[1]
        if sql.startswith("sql"):
            sql = sql[3:]
    sql = sql.strip()
    
    return sql


def format_results(df: pd.DataFrame, question: str) -> str:
    """Format query results into a readable response."""
    llm = get_llm()
    
    # Convert DataFrame to string representation
    if len(df) == 0:
        data_str = "Aucun résultat trouvé."
    elif len(df) == 1 and len(df.columns) == 1:
        # Single value result
        data_str = str(df.iloc[0, 0])
    else:
        data_str = df.to_markdown(index=False)
    
    prompt = f"""Analyse ces résultats et formule une réponse claire à la question.

QUESTION: {question}

DONNÉES:
{data_str}

Fournis:
1. La réponse directe à la question
2. Les chiffres clés avec unités
3. Une brève interprétation métier si pertinent

RÉPONSE:"""
    
    response = llm.invoke([HumanMessage(content=prompt)])
    return response.content


def data_agent_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Data analysis agent node.
    
    Generates SQL, executes queries, and formats results.
    """
    question = state["messages"][-1] if state["messages"] else ""
    
    try:
        # Get database schema
        schema = get_table_schemas()
        
        # Generate SQL query
        sql = generate_sql_query(question, schema)
        
        # Execute query
        df, error = execute_query(sql)
        
        if error:
            answer = f"❌ Erreur SQL: {error}\n\nRequête générée:\n```sql\n{sql}\n```"
            data_results = {
                "success": False,
                "error": error,
                "sql": sql
            }
        else:
            # Format results
            formatted_answer = format_results(df, question)
            
            # Add SQL query for transparency
            answer = f"{formatted_answer}\n\n📊 **Requête SQL exécutée:**\n```sql\n{sql}\n```"
            
            # Calculate summary stats if applicable
            stats = {}
            for col in df.select_dtypes(include=['number']).columns:
                stats[col] = compute_statistics(df, col)
            
            data_results = {
                "success": True,
                "sql": sql,
                "row_count": len(df),
                "columns": list(df.columns),
                "data": df.to_dict(orient="records") if len(df) <= 20 else df.head(20).to_dict(orient="records"),
                "statistics": stats
            }
            
            # Store DataFrame in session for VizAgent
            st.session_state["last_query_df"] = df
            
    except Exception as e:
        answer = f"❌ Erreur lors de l'analyse: {str(e)}"
        data_results = {
            "success": False,
            "error": str(e)
        }
    
    return {
        "data_results": data_results,
        "messages": [f"[DataAgent] {answer}"],
        "final_answer": answer
    }
