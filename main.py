from fastapi import FastAPI, HTTPException
import requests
from bs4 import BeautifulSoup
from typing import Optional, List, Dict

app = FastAPI(title="Gold Price & Currency API", description="API ราคาทองคำและอัตราแลกเปลี่ยน", version="3.1.0")

# --- Configuration ---
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

# --- Helper Functions (Internal) ---

def get_html(url):
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.encoding = "utf-8"
        if response.status_code == 200:
            return BeautifulSoup(response.text, 'html.parser')
    except Exception as e:
        print(f"Error accessing {url}: {e}")
    return None

def _get_thb_rate():
    """ดึงข้อมูลค่าเงินบาทจาก Thaigold"""
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

def _scrape_update_list():
    """ฟังก์ชันกลางสำหรับดึงข้อมูลราคาทอง"""
    url = "https://www.goldtraders.or.th/UpdatePriceList.aspx"
    soup = get_html(url)
    
    data_rows = []
    
    if not soup:
        return None

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
                        "date_time": dt,
                        "no": int(no),
                        "gold_bar": {
                            "buy": cols[2].text.strip(),
                            "sell": cols[3].text.strip()
                        },
                        "gold_ornament": {
                            "buy": cols[4].text.strip(),
                            "sell": cols[5].text.strip()
                        },
                        "spot": cols[6].text.strip(),
                        "change": cols[8].text.strip()
                    }
                    data_rows.append(record)
    
    return data_rows

# --- API Endpoints ---

@app.get("/")
def read_root():
    return {"message": "Gold & Currency API is running"}

@app.get("/api/latest")
def get_latest_market_data():
    """
    ดึงข้อมูลตลาดล่าสุด (รวมทั้งราคาทองและค่าเงินบาท)
    """
    gold_data_list = _scrape_update_list()
    latest_gold = gold_data_list[0] if gold_data_list else None
    currency_data = _get_thb_rate()

    if not latest_gold and not currency_data:
         raise HTTPException(status_code=503, detail="Service unavailable")

    return {
        "gold": latest_gold,
        "currency": currency_data
    }

@app.get("/api/gold")
def get_gold_only():
    """
    ดึงเฉพาะราคาทองคำล่าสุด (ไม่มีค่าเงิน)
    """
    data = _scrape_update_list()
    
    if not data:
        raise HTTPException(status_code=503, detail="Cannot access goldtraders website")
        
    return data[0]

@app.get("/api/currency")
def get_currency_only():
    """
    ดึงเฉพาะค่าเงินบาทอย่างเดียว
    """
    data = _get_thb_rate()
    if not data:
        raise HTTPException(status_code=503, detail="Cannot fetch currency data")
    return data

@app.get("/api/updates")
def get_price_updates():
    """
    ตารางราคาทองย้อนหลังระหว่างวัน
    """
    data = _scrape_update_list()
    if data is None:
        raise HTTPException(status_code=503, detail="Cannot access goldtraders website")
    return {"count": len(data), "data": data}

@app.get("/api/jewelry")
def get_jewelry_prices():
    """
    ตารางราคาทองรูปพรรณชนิดอื่นๆ
    """
    url = "https://www.goldtraders.or.th/DailyPrices.aspx"
    soup = get_html(url)
    
    if not soup:
        raise HTTPException(status_code=503, detail="Cannot access daily prices")

    results = []
    target_table = None
    tables = soup.find_all("table")
    for table in tables:
        if "ชนิดทอง" in table.text:
            target_table = table
            break
    
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