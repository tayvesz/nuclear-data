# ☢️ Chatbot Données Nucléaires

**Assistant IA Multi-Agent pour l'Analyse de Données Nucléaires**

Un système RAG agentique combinant recherche documentaire, analyse de données opérationnelles et visualisation intelligente.

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-red)
![LangGraph](https://img.shields.io/badge/LangGraph-0.0.40+-green)

## 🎯 Fonctionnalités

### Architecture Multi-Agent (Supervisor Pattern)

```
User Question
     ↓
 Supervisor (LLM Router)
     ↓
   ┌─────────────┬──────────────┬──────────────┐
   ↓             ↓              ↓              ↓
DocAgent    DataAgent      VizAgent      SummaryAgent
(RAG)       (SQL/stats)    (Plotly)      (Synthèse)
```

### Les 4 Agents Spécialisés

| Agent | Rôle | Outils |
|-------|------|--------|
| 📄 **DocAgent** | Recherche documentaire RAG | `search_technical_docs` |
| 📊 **DataAgent** | Analyse quantitative SQL | `query_operational_data` |
| 📈 **VizAgent** | Génération graphiques | `generate_plotly_chart` |
| 📝 **SummaryAgent** | Synthèse multi-sources | `generate_summary` |

## 🚀 Déploiement Streamlit Cloud (Gratuit)

### Étape 1: Pousser sur GitHub
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/VOTRE_USERNAME/chatbot-nucleaire.git
git push -u origin main
```

### Étape 2: Déployer sur Streamlit Cloud
1. Aller sur [share.streamlit.io](https://share.streamlit.io)
2. Cliquer "New app"
3. Sélectionner votre repo GitHub
4. Main file path: `app.py`
5. Dans "Advanced settings" > "Secrets", ajouter:
```toml
[groq]
api_key = "gsk_VOTRE_CLE_GROQ"
```

### Étape 3: C'est déployé ! 🎉

## 💻 Installation Locale

```bash
# Cloner le repo
git clone https://github.com/your-username/chatbot-nucleaire.git
cd chatbot-nucleaire

# Créer environnement virtuel avec uv
uv venv
source .venv/bin/activate

# Installer dépendances
uv pip install -r requirements.txt

# Configurer les secrets
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Éditer avec votre clé Groq

# Initialiser les données
python setup.py --db-only

# Lancer l'application
streamlit run app.py
```

## 📊 Exemples de Questions

### Documentation (DocAgent)
- "Quelle est la procédure de maintenance des pompes primaires ?"
- "Quels sont les critères de sûreté nucléaire ?"

### Analyse de données (DataAgent)
- "Combien de réacteurs sont opérationnels en France ?"
- "Statistiques des incidents par sévérité"

### Visualisation (VizAgent)
- "Graphique des maintenances par type d'équipement"
- "Distribution des incidents par catégorie"

## 📁 Structure du Projet

```
chatbot-nucleaire/
├── app.py                    # Interface Streamlit
├── agents/
│   ├── supervisor.py         # Routeur LangGraph
│   ├── doc_agent.py          # Agent RAG
│   ├── data_agent.py         # Agent SQL
│   ├── viz_agent.py          # Agent Plotly
│   └── summary_agent.py      # Agent synthèse
├── tools/                    # Outils des agents
├── ingest/                   # Pipelines données
├── data/                     # Données (auto-générées)
├── .streamlit/
│   └── secrets.toml          # Clés API (gitignored)
└── requirements.txt
```

## 🛠️ Technologies

- **LLM**: Groq (Llama 3.3 70B) - Gratuit
- **Embeddings**: HuggingFace (local) - Gratuit
- **Framework**: LangGraph
- **Vector Store**: ChromaDB
- **Visualisation**: Plotly
- **Interface**: Streamlit

## 📈 Données Simulées

Le projet inclut des données réalistes :
- **58 réacteurs** du parc nucléaire français
- **~50,000 maintenances** sur 10 ans
- **~10,000 incidents** avec sévérité INES
- **Capteurs temps réel** (température, pression, puissance)

## 📄 Licence

MIT License - Projet de démonstration
