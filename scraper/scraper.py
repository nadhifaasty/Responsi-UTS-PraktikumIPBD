from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from datetime import datetime
import json
import csv
import time
import os

def init_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-web-security")
    options.add_argument("--allow-running-insecure-content")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--start-maximized")
    options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    options.add_experimental_option("useAutomationExtension", False)
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/147.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(60)
    
    # Hapus tanda webdriver dari navigator
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })
    
    return driver

def scrape_wired():
    driver = init_driver()
    articles = []
    
    urls_to_scrape = [
        "https://www.wired.com/",
        "https://www.wired.com/category/science/",
        "https://www.wired.com/category/security/",
        "https://www.wired.com/category/business/",
        "https://www.wired.com/category/politics/",
        "https://www.wired.com/category/culture/",
    ]
    
    for page_url in urls_to_scrape:
        print(f"Scraping: {page_url}")
        try:
            driver.get(page_url)
        except Exception as e:
            print(f"[!] Timeout load halaman {page_url}, coba lanjut...")
            pass
        
        time.sleep(5)  # kasih waktu lebih buat render)
        
        # Scroll dulu biar konten lazy-load muncul
        for _ in range(8):
            driver.execute_script("window.scrollBy(0, 800);")
            time.sleep(1.2)
        
        # Selector baru sesuai struktur Wired.com sekarang
        cards = driver.find_elements(By.CSS_SELECTOR, "[class*='SummaryItemWrapper'], [class*='summary-item'], [class*='SummaryItem']")
        
        # Fallback kalau masih 0
        if len(cards) == 0:
            cards = driver.find_elements(By.CSS_SELECTOR, "a[href*='/story/']")
        
        print(f"Ditemukan {len(cards)} elemen di {page_url}")
        
        for card in cards:
            try:
                # Kalau fallback (tag <a>), ambil langsung
                tag = card.tag_name
                if tag == "a":
                    url = card.get_attribute("href")
                    try:
                        title = card.find_element(By.CSS_SELECTOR, "h2, h3, [class*='title'], [class*='Title']").text.strip()
                    except:
                        title = card.text.strip().split("\n")[0]
                    description = ""
                    author = "By Unknown"
                else:
                    try:
                        title = card.find_element(By.CSS_SELECTOR, "h2, h3, [class*='title'], [class*='Title']").text.strip()
                    except:
                        title = ""
                    
                    try:
                        url = card.find_element(By.TAG_NAME, "a").get_attribute("href")
                    except:
                        url = ""
                    
                    try:
                        description = card.find_element(By.CSS_SELECTOR, "p, [class*='dek'], [class*='Dek']").text.strip()
                    except:
                        description = ""
                    
                    try:
                        author_el = card.find_element(By.CSS_SELECTOR, "[class*='author'], [class*='Author'], [class*='byline'], [class*='Byline'], [class*='contributor'], [class*='Contributor']")
                        author = author_el.text.strip()
                        if author and not author.startswith("By"):
                            author = "By" + author
                    except:
                        author = "By Unknown"
                
                if not title or not url:
                    continue
                
                if not url.startswith("https://www.wired.com"):
                    continue
                
                if not any(a["url"] == url for a in articles):
                    articles.append({
                        "title": title,
                        "url": url,
                        "description": description,
                        "author": author,
                        "scraped_at": datetime.now().isoformat(),
                        "source": "Wired.com"
                    })
                    
            except Exception as e:
                print(f"Error parsing card: {e}")
                continue
        
        print(f"Total artikel sejauh ini: {len(articles)}")
        time.sleep(2)
        
        if len(articles) >= 50:
            print("udah dapat 50+ artikel, stop scraping.")
            break
    
    driver.quit()
    return articles

def save_to_json(articles, session_id):
    output = [
        {
            "session_id": session_id,
            "timestamp": datetime.now().isoformat(),
            "articles_count": len(articles),
            "articles": articles
        }
    ]
    
    output_path = os.path.join(os.path.dirname(__file__), "../api/articles.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print(f"Tersimpan ke articles.json")

def save_to_csv(articles):
    output_path = os.path.join(os.path.dirname(__file__), "../api/articles.csv")
    
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["title", "url", "description", "author", "scraped_at", "source"])
        writer.writeheader()
        writer.writerows(articles)
    
    print(f"Tersimpan ke articles.csv")

if __name__ == "__main__":
    print("mulai scraping Wired.com...")
    articles = scrape_wired()
    print(f"Total artikel terkumpul: {len(articles)}")
    
    session_id = f"wired_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    save_to_json(articles, session_id)
    save_to_csv(articles)
    print("Scraping selesai")