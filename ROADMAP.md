# 🗺️ Roadmap - Scraping Animals

## 📋 Project Objective

Build a web application that displays scraped animal data from [a-z-animals.com](https://a-z-animals.com), with database storage and Docker containerization.

---

## ✅ Progress Status

| Step | Status | Description |
|------|--------|-------------|
| 1. Scraping | ✅ Done | Animal list + Details (252 animaux) |
| 1b. Scraper Unit Tests | ✅ Done | 9 tests implemented & passing |
| 1c. CI Pipeline | ✅ Done | lint + test passing on GitHub |
| 2. Docker Compose | ✅ Done | Dockerfiles complete |
| 3. MongoDB Storage | ✅ Done | 252 animals in MongoDB |
| 4. Web Application (TDD) | 🔲 To Do | Tests skeleton, **app folder empty** |
| 5. Elasticsearch | 🔲 To Do | Search engine (bonus) |
| 6. Documentation | 🔲 To Do | README minimal (18 bytes) |

---

## 📦 Detailed Steps

### Step 1: Scraping

#### Phase 1: Animal List ✅

- [x] Create Scrapy spider (`animals_spider.py`)
- [x] Bypass anti-bot protection with `scrapy-impersonate`
- [x] Retrieve animal list (name + URL)
- [x] 3019 animals indexed

**Current Data**:
```json
{
    "animal_name": "Tiger",
    "url": "https://a-z-animals.com/animals/tiger/",
    "source_page": "..."
}
```

#### Phase 2: Animal Details ✅

**Approach**: Modify existing spider to follow each URL and extract detailed data.

- [x] Add `parse_animal_detail()` method
- [x] Extract information from each animal page:
  - Scientific name
  - Description
  - Key Facts
  - Conservation Status
  - Habitat
  - Diet
  - ~~Main image~~ *(removed - too complex)*
- [x] Limit to ~200 animals for the project (10/letter = 260)

**Target Data**:
```json
{
    "animal_name": "Tiger",
    "scientific_name": "Panthera Tigris",
    "description": "The tiger is the largest...",
    "key_facts": ["Largest living cat species", ...],
    "conservation_status": "Endangered",
    "habitat": "Asia",
    "diet": "Carnivore"
}
```

**Performance Optimizations**:
- `DOWNLOAD_DELAY`: 0.5s (reduced from 2s)
- Sampling: X animals per letter (26 letters)
- Example: 10 animals/letter = 260 animals total

---

### Step 2: Docker Compose ✅ Done

- [x] Configure MongoDB
- [x] Configure Elasticsearch + Kibana
- [x] Configure network between services
- [x] Complete scraper Dockerfile
- [x] Complete webapp Dockerfile

---

### Step 1b: Scraper Unit Tests ✅ Done

> [!IMPORTANT]
> **Critical step**: Validate JSON format before any DB insertion.

- [x] Create `tests/test_spider.py`
- [x] Test `parse_animal_detail()` with mocked HTML responses
- [x] Verify exported data format (required fields present)
- [x] Validate JSON with schema
- [x] Test spider configuration (name, domains, settings)

**Tests implemented (9 total)**:
- `TestAnimalsSpider`: 4 tests (parse_animal_detail, required fields, limit)
- `TestJsonValidation`: 2 tests (schema, null names)
- `TestSpiderConfiguration`: 3 tests (name, domains, settings)

---

### Step 1c: CI Pipeline ✅ Done

> [!NOTE]
> **Pipeline verified and passing on GitHub Actions!**

- [x] Create `.github/workflows/ci.yml`
- [x] `lint` job: flake8 on each push
- [x] `test` job: pytest with MongoDB Service Container
- [x] Verify pipeline on GitHub ✅

**Dev/Prod Parity**: Uses a real MongoDB instance (not mongomock) via Docker Service Container in CI.

---

### Step 3: MongoDB Storage ✅ Done

- [x] Add `pymongo` to dependencies
- [x] Create Scrapy Item Pipeline for MongoDB (`pipelines.py`)
- [x] Test data insertion
- [x] Verify data in MongoDB (252 animals inserted)

**Integration Tests (real MongoDB instance)**:
- [x] Test Spider → MongoDB pipeline with Docker Service Container
- [x] Verify connection and insertion
- [x] Ensure Dev/Prod parity

---

### Step 4: Web Application (TDD) 🔲

**Technologies**: Dash (Python)

> [!NOTE]
> **TDD Approach**: Write tests BEFORE code.

**Step 1 - Tests First**:
- [x] Create `tests/test_webapp.py` *(file exists)*
- [/] Define tests for `/animals` route *(skeleton, TODO in code)*
- [/] Define tests for `/animals/<id>` route *(skeleton, TODO in code)*
- [/] Define tests for statistics *(skeleton, TODO in code)*

**Step 2 - Implementation**:
- [ ] Create Dash application *(app folder currently empty)*
- [ ] Home page with statistics
- [ ] Animal list with pagination
- [ ] Detailed animal page
- [ ] Charts (distribution by conservation status, etc.)
- [ ] Filters and search

---

### Step 5: Elasticsearch (Bonus) 🔲

- [ ] Index animals in Elasticsearch
- [ ] Create search endpoint
- [ ] Integrate search into web interface

---

### Step 6: Documentation 🔲

- [ ] Complete README.md
- [ ] Application screenshots
- [ ] Deployment instructions
- [ ] Push to public GitHub

---

## 🎯 Requirements Checklist

### Mandatory

- [x] Scrape data from a website (Phase 1 ✅, Phase 2 ✅)
- [ ] Store data in a database (MongoDB)
- [ ] Python Web Application (Dash)
- [ ] Optimal display (charts, search)
- [ ] Services in Docker containers
- [ ] Technical and functional documentation
- [ ] Public GitHub repository

### Bonus

- [ ] Real-time scraping on startup
- [x] Use of docker-compose
- [ ] Search engine with Elasticsearch

---

## 👥 Team

- **Partner**: [To be completed]

---

## 📅 Suggested Planning

| Day | Tasks |
|-----|-------|
| D1 | ✅ Scraping Phase 1 + Docker Compose |
| D2 | Scraping Phase 2 + MongoDB Storage |
| D3 | Web Application (structure + pages) |
| D4 | Charts + Search |
| D5 | Elasticsearch (bonus) + Documentation |
| D6 | Final tests + GitHub Deployment |
