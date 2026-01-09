from fastapi import FastAPI, HTTPException
import requests
from bs4 import BeautifulSoup
from typing import Optional, List, Dict
import time # เพิ่ม time เข้ามาเพื่อจับเวลา

app = FastAPI(title="Gold Price & Currency API", description="API พร้อมระบบ Caching", version="4.0.0")

# --- Configuration ---
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# --- CACHE STORAGE (ตัวเก็บข้อมูลชั่วคราว) ---
CACHE_DURATION = 120  # เก็บข้อมูลไว้ 120 วินาที (2 นาที)
_cache_gold = {"data": None, "timestamp": 0}
_cache_currency = {"data": None, "timestamp": 0}

# --- Helper Functions ---

def get_html(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.encoding = "utf-8"
        if response.status_code == 200:
            return BeautifulSoup(response.text, 'html.parser')
    except Exception as e:
        print(f"Error accessing {url}: {e}")
    return None

def _fetch_thb_rate_fresh():
    """ฟังก์ชันวิ่งไปดึงค่าเงินจริง (ไม่ผ่าน Cache)"""
    url = "https://www.thaigold.info/RealTimeDataV2/gtdata_.txt"
    try:
        response = requests.get(url, headers=HEADERS, timeout=5)
        if response.status_code == 200:
            data_list = response.json()
            for item in data_list:
                if item.get("name") == "THB":
                    return item 
    except Exception as e:
        print(f"Error accessing currency data: {e}")
    return None

def _fetch_gold_list_fresh():
    """ฟังก์ชันวิ่งไปดึงราคาทองจริง (ไม่ผ่าน Cache)"""
    url = "https://www.goldtraders.or.th/UpdatePriceList.aspx"
    soup = get_html(url)
    
    data_rows = []
    if not soup: return None

    target_table = None
    tables = soup.find_all("table")
    for table in tables:
        if "ครั้งที่" in table.text and "Gold Spot" in table.text:
            target_table = table
            break
    
    if target_table:
        rows = target_table.find_all("tr")
        for row in rows:
            cols = row.find_all("td")
            if len(cols) >= 9:
                raw_dt = cols[0].text.strip()
                dt = " ".join(raw_dt.split())
                no = cols[1].text.strip()
                if no.isdigit():
                    record = {
                        "date_time": dt, "no": int(no),
                        "gold_bar": { "buy": cols[2].text.strip(), "sell": cols[3].text.strip() },
                        "gold_ornament": { "buy": cols[4].text.strip(), "sell": cols[5].text.strip() },
                        "spot": cols[6].text.strip(), "change": cols[8].text.strip()
                    }
                    data_rows.append(record)
    return data_rows

# --- SMART DATA RETRIEVAL (ตัวจัดการ Cache) ---

def get_gold_data_smart():
    global _cache_gold
    current_time = time.time()
    
    # ถ้าข้อมูลเก่าเกิน 2 นาที หรือยังไม่มีข้อมูล ให้ไปดึงใหม่
    if current_time - _cache_gold["timestamp"] > CACHE_DURATION or _cache_gold["data"] is None:
        print("Fetching new GOLD data from website...") # Log ดูว่ามีการดึงใหม่
        new_data = _fetch_gold_list_fresh()
        if new_data:
            _cache_gold["data"] = new_data
            _cache_gold["timestamp"] = current_time
    
    return _cache_gold["data"]

def get_currency_data_smart():
    global _cache_currency
    current_time = time.time()
    
    if current_time - _cache_currency["timestamp"] > CACHE_DURATION or _cache_currency["data"] is None:
        print("Fetching new CURRENCY data from website...")
        new_data = _fetch_thb_rate_fresh()
        if new_data:
            _cache_currency["data"] = new_data
            _cache_currency["timestamp"] = current_time
            
    return _cache_currency["data"]

# --- API Endpoints ---

@app.get("/")
def read_root():
    return {"message": "Gold API with Caching System is running"}

@app.get("/api/latest")
def get_latest_market_data():
    gold_list = get_gold_data_smart()
    latest_gold = gold_list[0] if gold_list else None
    currency = get_currency_data_smart()

    if not latest_gold and not currency:
         raise HTTPException(status_code=503, detail="Service unavailable")

    return { "gold": latest_gold, "currency": currency }

@app.get("/api/gold")
def get_gold_only():
    data = get_gold_data_smart()
    if not data:
        raise HTTPException(status_code=503, detail="Cannot access goldtraders website")
    return data[0]

@app.get("/api/currency")
def get_currency_only():
    data = get_currency_data_smart()
    if not data:
        raise HTTPException(status_code=503, detail="Cannot fetch currency data")
    return data

@app.get("/api/updates")
def get_price_updates():
    data = get_gold_data_smart()
    if data is None:
        raise HTTPException(status_code=503, detail="Cannot access goldtraders website")
    return {"count": len(data), "data": data}

@app.get("/api/jewelry")
def get_jewelry_prices():
    # อันนี้ดึงสด เพราะคนเรียกไม่บ่อย ไม่จำเป็นต้อง Cache ก็ได้ หรือจะทำก็ได้ครับ
    url = "https://www.goldtraders.or.th/DailyPrices.aspx"
    soup = get_html(url)
    if not soup: raise HTTPException(status_code=503, detail="Cannot access daily prices")
    results = []
    target_table = None
    tables = soup.find_all("table")
    for table in tables:
        if "ชนิดทอง" in table.text:
            target_table = table; break
    if target_table:
        rows = target_table.find_all("tr")
        for row in rows[1:]:
            cols = row.find_all("td")
            if len(cols) >= 4:
                results.append({
                    "type": cols[0].text.strip(),
                    "per_gram_buy": cols[1].text.strip(),
                    "per_baht_buy": cols[2].text.strip(),
                    "per_baht_sell": cols[3].text.strip()
                })
    return {"data": results}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)