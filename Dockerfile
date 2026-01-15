# Utiliser une image Python légère
FROM python:3.11-slim

# Définir le répertoire de travail
WORKDIR /app

# Installer les dépendances système nécessaires
# build-essential pour compiler certaines libs
# git pour cloner si besoin
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    software-properties-common \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copier les fichiers de dépendances
COPY requirements.txt .

# Installer les dépendances Python
RUN pip3 install --no-cache-dir -r requirements.txt

# Copier tout le code du projet
COPY . .

# Initialiser la base de données au build (optionnel mais utile pour une démo)
# On utilise --db-only pour ne pas bloquer sur les clés API manquantes au build
RUN python3 setup.py --db-only

# Exposer le port par défaut de Streamlit
EXPOSE 8501

# Vérification de santé (Healthcheck)
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Commande de démarrage
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
