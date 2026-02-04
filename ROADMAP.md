# 🗺️ Roadmap - Scraping Animals

## 🎯 Objectif

Construire une application web qui **scrape** les données d’animaux depuis [a-z-animals.com](https://a-z-animals.com), les **stocke dans MongoDB**, les **indexe dans Elasticsearch**, et les **expose via Streamlit**.

---

## ✅ Statut global

| Étape | Statut | Description |
|------|--------|-------------|
| 1. Scraping | ✅ Fait | Liste + détails (≈252 animaux) |
| 2. Docker Compose | ✅ Fait | Dockerfiles et orchestration | 
| 3. MongoDB | ✅ Fait | Insertion + validation des données |
| 4. Web App | ✅ Fait | Streamlit avec filtres, stats, exports |
| 5. Elasticsearch | ✅ Fait | Indexation + recherche intégrée |
| 6. Documentation | ✅ Fait | README à jour |

---

## 🧩 Détails par module

### 1) Scraping (Scrapy) ✅

- [x] Spider `animals_spider.py`
- [x] Contournement anti-bot via `scrapy-impersonate`
- [x] Extraction des champs détaillés (scientific name, habitat, diet, etc.)
- [x] Limite d’échantillonnage paramétrable (ex. 10/lettre)

**Exemple de données** :
```json
{
  "animal_name": "Tiger",
  "scientific_name": "Panthera tigris",
  "description": "The tiger is the largest...",
  "key_facts": ["Largest living cat species"],
  "conservation_status": "Endangered",
  "habitat": "Asia",
  "diet": "Carnivore"
}
```

### 2) Docker Compose ✅

- [x] MongoDB + Elasticsearch + Kibana + Webapp
- [x] Réseaux et dépendances inter-services
- [x] Dockerfiles du scraper et de l’app Streamlit

### 3) MongoDB ✅

- [x] Pipeline d’insertion Scrapy
- [x] Tests d’intégration sur une vraie instance MongoDB
- [x] Vérification des données insérées

### 4) Web App (Streamlit) ✅

- [x] Filtres (habitat, diet, statut)
- [x] Table interactive + export CSV
- [x] Graphiques (distribution)
- [x] Fiche détaillée par animal

### 5) Elasticsearch ✅

- [x] Indexation des documents
- [x] Recherche fuzzy via `SearchClient`
- [x] Fallback si ES indisponible

### 6) Documentation ✅

- [x] README mis à jour
- [ ] Ajouter des instructions de déploiement

## ✅ Checklist des exigences

### Obligatoire

- [x] Scraping d’un site web
- [x] Stockage en base (MongoDB)
- [x] Web app Python (Streamlit)
- [x] Visualisations et recherche
- [x] Services conteneurisés
- [x] Documentation technique/func
- [ ] Dépôt GitHub public

### Bonus

- [ ] Scraping au démarrage
- [x] docker-compose
- [x] Recherche Elasticsearch

---

## 👥 Équipe

- **Partenaire** : Keren BENADIBA & Wilfried LAFAYE

---

## 🗓️ Planning indicatif

| Jour | Tâches |
|-----|--------|
| J1 | Scraping phase 1 + Docker Compose |
| J2 | Détails + MongoDB |
| J3 | Web app (structure + pages) |
| J4 | Graphiques + recherche |
| J5 | Elasticsearch + documentation |
| J6 | Tests finaux + publication |
