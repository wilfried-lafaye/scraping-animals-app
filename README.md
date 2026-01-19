# 🦁 Scraping Animals

Application web de visualisation de données animales, construite avec Scrapy, MongoDB, et Streamlit.

## 📋 Description

Ce projet scrape les données de [a-z-animals.com](https://a-z-animals.com) et les affiche dans une interface web interactive avec :
- Recherche par nom
- Carte choroplèthe de distribution mondiale
- Fiches détaillées par animal
- Filtres par régime alimentaire et habitat

## 🚀 Installation

### Prérequis
- Docker & Docker Compose
- Python 3.11+

### Lancement

```bash
# Cloner le repo
git clone https://github.com/[username]/scraping-animals.git
cd scraping-animals

# Lancer les services
docker-compose up -d

# Importer les données (si nécessaire)
docker cp scrapy/data/animals.json scraping_webapp:/app/animals.json
docker exec scraping_webapp python3 /app/import_script.py
```

L'application sera accessible sur **http://localhost:8501**

## 🏗️ Architecture

```
scraping-animals/
├── scrapy/          # Spider Scrapy
├── webapp/          # Application Streamlit
├── scripts/         # Utilitaires d'import/nettoyage
├── tests/           # Tests unitaires
└── docker-compose.yml
```

## 🛠️ Technologies

- **Scraping**: Scrapy + scrapy-impersonate
- **Database**: MongoDB 7.0
- **Frontend**: Streamlit
- **Containerisation**: Docker Compose

## 📊 Données

- **191 animaux** actuellement dans la base
- Informations : nom, classification, faits, localisation géographique

## 👥 Équipe

- Projet réalisé dans le cadre du cours Data Engineering - ESIEE Paris E4

## 📄 License

MIT