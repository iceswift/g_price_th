# 🏆 Thai Gold Price API (FastAPI)

A lightweight RESTful API that scrapes real-time gold prices from the **Gold Traders Association of Thailand** and USD/THB exchange rates. Built with **FastAPI** and **BeautifulSoup4**.

## ✨ Features
- **Real-time Data:** Fetches the latest gold bar and ornament prices (96.5%).
- **Smart Caching:** Implements a 2-minute caching mechanism to reduce server load and prevent IP bans.
- **Currency Rates:** Provides real-time USD/THB exchange rates.
- **Intraday Updates:** Access historical price changes throughout the day.
- **Fast & Async:** High performance powered by FastAPI.

## 🚀 API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/latest` | Get latest gold prices & currency rates (Combined) |
| `GET` | `/api/gold` | Get latest gold prices only |
| `GET` | `/api/currency` | Get USD/THB exchange rate only |
| `GET` | `/api/updates` | Get intraday price change table |
| `GET` | `/api/jewelry` | Get other jewelry prices |
| `GET` | `/docs` | Interactive Swagger UI documentation |

## 🛠 Tech Stack
- **Python 3.9+**
- **FastAPI** (Web Framework)
- **BeautifulSoup4** (Web Scraping)
- **Requests** (HTTP Client)
- **Uvicorn** (ASGI Server)

## 📦 Installation & Run

1. **Clone the repository**
   ```bash
   git clone [https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git](https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git)
   cd YOUR_REPO_NAME