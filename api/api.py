from fastapi import FastAPI, HTTPException
from typing import List, Dict, Any
import json
import os


app = FastAPI(
    title="Wired Articles API",
    description="API untuk menyajikan data scraping Wired.com",
    version="1.0.0"
)

JSON_PATH = os.path.join(os.path.dirname(__file__), "articles.json")

def load_articles() -> List[Dict[str, Any]]:
    if not os.path.exists(JSON_PATH):
        raise HTTPException(
            status_code=404,
            detail="File articles.json tidak ditemukan. Jalanin scraper dulu."
        )
    
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    all_articles = []
    for session in data:
        all_articles.extend(session.get("articles", []))
    
    return all_articles

@app.get("/")
def root():
    return {"message": "Wired Articles API is running"}

@app.get("/articles")
def get_articles():
    articles = load_articles()
    return {
        "status": "success",
        "total": len(articles),
        "data": articles
    }