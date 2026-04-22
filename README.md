# Wired Data Pipeline
Pipeline data end-to-end untuk mengambil, memproses, dan menyimpan data artikel dari Wired.com secara otomatis.

---

## Tools & Teknologi

- Python 3.11
- Selenium (Web Scraping)
- FastAPI (API Service)
- Docker & Docker Compose
- Apache Airflow 2.9.1 (Orchestration)
- PostgreSQL 15 (Database)
- SQL (Reporting)

---

## Struktur Project
wired-pipeline/
│
├── scraper/
│   └── scraper.py        ← Selenium scraper
│
├── api/
│   ├── api.py            ← FastAPI service
│   ├── articles.json     ← Hasil scrape (JSON)
│   └── articles.csv      ← Hasil scrape (CSV)
│
├── dags/
│   └── wired_dag.py      ← Airflow DAG
│
└── docker-compose.yml    ← Airflow + PostgreSQL

---

## Alur Pipeline
Scraping (Selenium) → JSON/CSV → FastAPI → Airflow DAG → PostgreSQL → SQL Query

---

## Cara Menjalankan

### 1. Install Dependencies
```bash
pip install selenium fastapi uvicorn requests psycopg2-binary
```

### 2. Jalankan Scraper
```bash
python scraper/scraper.py
```
Selenium akan membuka Chrome secara otomatis dan scraping minimal 50 artikel dari Wired.com. Hasil disimpan ke `api/articles.json` dan `api/articles.csv`.

### 3. Jalankan FastAPI
```bash
uvicorn api.api:app --reload --port 8000
```
Akses API:
http://127.0.0.1:8000/articles

### 4. Jalankan Docker (Airflow + PostgreSQL)
```bash
docker compose up -d
```
Akses Airflow:
http://localhost:8080
Login:
username: admin
password: admin

### 5. Jalankan DAG
- Masuk ke Airflow UI
- Aktifkan DAG `wired_pipeline_dag`
- Klik **Trigger DAG**

### 6. Cek Database
Connect ke PostgreSQL:
Host     : localhost
Port     : 5432
User     : wired_user
Password : wired_pass
Database : wired_db

---

## SQL Query (Reporting)

### Query 1 — Clean Author
```sql
SELECT 
    title,
    TRIM(REPLACE(author, 'By', '')) AS clean_author
FROM wired_articles;
```

### Query 2 — Top 3 Author
```sql
SELECT 
    TRIM(REPLACE(author, 'By', '')) AS clean_author,
    COUNT(*) AS total_articles
FROM wired_articles
WHERE author IS NOT NULL AND author != ''
GROUP BY clean_author
ORDER BY total_articles DESC
LIMIT 3;
```

### Query 3 — Keyword Search
```sql
SELECT 
    title,
    author,
    description
FROM wired_articles
WHERE 
    title ILIKE '%AI%' OR title ILIKE '%Climate%' OR title ILIKE '%Security%'
    OR description ILIKE '%AI%' OR description ILIKE '%Climate%' OR description ILIKE '%S
