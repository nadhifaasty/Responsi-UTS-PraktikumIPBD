from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import requests
import psycopg2

DB_CONFIG = {
    "host": "postgres",
    "port": 5432,
    "database": "wired_db",
    "user": "wired_user",
    "password": "wired_pass"
}

API_URL = "http://host.docker.internal:8000/articles"

default_args = {
    "owner": "mahasiswa",
    "depends_on_past": False,
    "start_date": datetime(2026, 4, 22),
    "email_on_failure": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=1),
}


def create_table():
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS wired_articles (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            url TEXT UNIQUE,
            description TEXT,
            author TEXT,
            scraped_at TIMESTAMP,
            source TEXT,
            inserted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    cursor.close()
    conn.close()
    print("[✓] Tabel wired_articles siap.")


def fetch_from_api(**context):
    print(f"[*] Fetching dari {API_URL}...")
    response = requests.get(API_URL, timeout=30)
    response.raise_for_status()

    data = response.json()
    articles = data.get("data", [])

    print(f"[✓] Berhasil fetch {len(articles)} artikel.")
    context["ti"].xcom_push(key="raw_articles", value=articles)


def transform_data(**context):
    articles = context["ti"].xcom_pull(key="raw_articles", task_ids="fetch_from_api")

    cleaned = []
    for article in articles:
        scraped_at_raw = article.get("scraped_at", "")
        try:
            dt = datetime.fromisoformat(scraped_at_raw)
            scraped_at = dt.strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError):
            scraped_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cleaned.append({
            "title": article.get("title", "").strip(),
            "url": article.get("url", "").strip(),
            "description": article.get("description", "").strip(),
            "author": article.get("author", "").strip(),
            "scraped_at": scraped_at,
            "source": article.get("source", "Wired.com")
        })

    print(f"[✓] Transformasi selesai, {len(cleaned)} artikel siap masuk DB.")
    context["ti"].xcom_push(key="clean_articles", value=cleaned)


def load_to_database(**context):
    articles = context["ti"].xcom_pull(key="clean_articles", task_ids="transform_data")

    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    inserted = 0
    skipped = 0

    for article in articles:
        try:
            cursor.execute("""
                INSERT INTO wired_articles (title, url, description, author, scraped_at, source)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (url) DO NOTHING;
            """, (
                article["title"],
                article["url"],
                article["description"],
                article["author"],
                article["scraped_at"],
                article["source"]
            ))
            if cursor.rowcount > 0:
                inserted += 1
            else:
                skipped += 1
        except Exception as e:
            print(f"[!] Error insert: {e}")
            continue

    conn.commit()
    cursor.close()
    conn.close()
    print(f"[✓] Selesai! {inserted} artikel diinsert, {skipped} duplikat dilewati.")


with DAG(
    dag_id="wired_pipeline_dag",
    default_args=default_args,
    description="Pipeline: API → Transform → PostgreSQL",
    schedule_interval="@daily",
    catchup=False,
    tags=["wired", "big-data", "ipbd"]
) as dag:

    task_create_table = PythonOperator(
        task_id="create_table",
        python_callable=create_table
    )

    task_fetch = PythonOperator(
        task_id="fetch_from_api",
        python_callable=fetch_from_api
    )

    task_transform = PythonOperator(
        task_id="transform_data",
        python_callable=transform_data
    )

    task_load = PythonOperator(
        task_id="load_to_database",
        python_callable=load_to_database
    )

    task_create_table >> task_fetch >> task_transform >> task_load