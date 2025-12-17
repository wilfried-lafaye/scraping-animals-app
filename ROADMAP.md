# 🗺️ Roadmap - Scraping Animals

## 📋 Project Objective

Build a web application that displays scraped animal data from [a-z-animals.com](https://a-z-animals.com), with database storage and Docker containerization.

---

## ✅ Progress Status

| Step | Status | Description |
|------|--------|-------------|
| 1. Scraping | ✅ Done | Animal list + Details |
| 1b. Scraper Unit Tests | 🚨 To Do | Validate JSON format before DB insertion |
| **1c. CI Pipeline** | 🚨 Priority | GitHub Actions: flake8 + pytest on each push |
| 2. Docker Compose | ✅ Done | Multi-service configuration |
| 3. MongoDB Storage | 🔲 To Do | Pipeline + Tests with real MongoDB instance |
| 4. Web Application (TDD) | 🔲 To Do | Tests first → then implementation |
| 5. Elasticsearch | 🔲 To Do | Search engine (bonus) |
| 6. Documentation | 🔲 To Do | Technical and functional README |

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

### Step 2: Docker Compose ✅

- [x] Configure MongoDB
- [x] Configure Elasticsearch + Kibana
- [x] Configure network between services
- [ ] Complete scraper Dockerfile
- [ ] Complete webapp Dockerfile

---

### Step 1b: Scraper Unit Tests 🚨

> [!IMPORTANT]
> **Critical step**: Validate JSON format before any DB insertion.

- [ ] Create `tests/test_spider.py`
- [ ] Test `parse_animal_detail()` with mocked HTML responses
- [ ] Verify exported data format (required fields present)
- [ ] Validate JSON with schema (optional)

---

### Step 1c: CI Pipeline 🚨

> [!IMPORTANT]
> **Immediate priority**: GitHub Actions pipeline configured!

- [x] Create `.github/workflows/ci.yml`
- [x] `lint` job: flake8 on each push
- [x] `test` job: pytest with MongoDB Service Container
- [ ] Verify pipeline on GitHub

**Dev/Prod Parity**: Uses a real MongoDB instance (not mongomock) via Docker Service Container in CI.

---

### Step 3: MongoDB Storage 🔲

- [ ] Add `pymongo` to dependencies
- [ ] Create Scrapy Item Pipeline for MongoDB
- [ ] Test data insertion
- [ ] Verify data in MongoDB

**Integration Tests (real MongoDB instance)**:
- [ ] Test Spider → MongoDB pipeline with Docker Service Container
- [ ] Verify connection and insertion
- [ ] Ensure Dev/Prod parity

---

### Step 4: Web Application (TDD) 🔲

**Technologies**: Dash (Python)

> [!NOTE]
> **TDD Approach**: Write tests BEFORE code.

**Step 1 - Tests First**:
- [ ] Create `tests/test_webapp.py`
- [ ] Define tests for `/animals` route (paginated list)
- [ ] Define tests for `/animals/<id>` route (detail page)
- [ ] Define tests for statistics (counts, charts)

**Step 2 - Implementation**:
- [ ] Create Dash application (make tests pass)
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
