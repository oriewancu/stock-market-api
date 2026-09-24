# Stock Market API

Backend REST API sederhana berbasis **Flask** untuk mengambil data saham Indonesia, saham Amerika Serikat, dan forex menggunakan [Yahoo Finance](https://finance.yahoo.com/) melalui library `yfinance`.

API ini juga menyediakan fitur untuk mendapatkan daftar ticker saham Indonesia berdasarkan rentang harga. Daftar ticker utama diambil dari GitHub Gist, dengan file Excel lokal sebagai fallback apabila Gist tidak dapat diakses.

---

## Features

- 🇮🇩 Data saham Indonesia / IDX
- 🇺🇸 Data saham Amerika Serikat
- 💱 Data Forex
- 📊 Historical OHLCV data
- 🏢 Informasi profil perusahaan
- 🔎 Filter saham berdasarkan rentang harga
- 📋 Bulk download harga saham IDX
- 🌐 CORS enabled
- ☁️ GitHub Gist sebagai sumber utama daftar ticker
- 📁 Excel sebagai fallback apabila Gist gagal
- ⚡ Optimized data period berdasarkan gaya trading

---

## Tech Stack

- Python
- Flask
- Flask-CORS
- yfinance
- Pandas
- OpenPyXL
- Requests

---

## Requirements

Pastikan sudah terinstall:

- Python 3.10+ recommended
- Internet connection
- pip

### Python Libraries

Semua dependency Python tersedia di:

```text
requirements.txt
```

Install dengan:

### Windows

```bash
py -m pip install -r requirements.txt
```

### Linux / macOS

```bash
python3 -m pip install -r requirements.txt
```

---

## Project Structure

```text
stock-market-api/
├── run.bat
├── server.py
├── requirements.txt
├── README.md
├── setup.bat
└── DaftarSaham.xlsx
```

> `DaftarSaham.xlsx` bersifat **fallback**. Aplikasi akan mencoba mengambil daftar ticker dari GitHub Gist terlebih dahulu.

---

# Installation

## 1. Clone Repository

```bash
git clone https://github.com/oriewancu/stock-market-api
cd stock-market-api
```

## 2. Install Dependencies

### Windows

```bash
py -m pip install -r requirements.txt
```

### Linux / macOS

```bash
python3 -m pip install -r requirements.txt
```

## 3. Run Server

### Windows

```bash
py server.py
```

### Linux / macOS

```bash
python3 server.py
```

Jika berhasil, akan muncul:

```text
🚀 Server berjalan di http://127.0.0.1:5000
```

API dapat diakses melalui:

```text
http://127.0.0.1:5000
```

---

# Windows First-Time Setup

Jika menjalankan project ini di komputer Windows yang baru pertama kali digunakan untuk development Python:

## 1. Install Python

Download dan install Python dari:

https://www.python.org/downloads/

Saat proses instalasi, pastikan opsi berikut dicentang:

```text
Add Python to PATH
```

Setelah instalasi selesai, buka terminal baru dan cek:

```bash
py --version
```

Kemudian:

```bash
py -m pip --version
```

Jika keduanya menampilkan versi, Python sudah siap digunakan.

## 2. Install Dependencies

Masuk ke folder project:

```bash
cd path\to\stock-market-api
```

Kemudian:

```bash
py -m pip install -r requirements.txt
```

## 3. Run

```bash
py server.py
```

---

# Linux / macOS First-Time Setup

Cek Python:

```bash
python3 --version
```

Cek pip:

```bash
python3 -m pip --version
```

Install dependency:

```bash
python3 -m pip install -r requirements.txt
```

Run server:

```bash
python3 server.py
```

---

# API Endpoints

## 1. Indonesian Stock

```http
GET /api/saham
```

Mengambil historical data saham Indonesia.

### Parameters

| Parameter | Required | Default | Description |
|---|---|---|---|
| `ticker` | No | `BBRI` | Kode saham IDX |
| `gaya` | No | `swing` | Mode data |

### Example

```text
/api/saham?ticker=BBRI
```

atau:

```text
/api/saham?ticker=BBRI&gaya=fast
```

### Supported Trading Modes

```text
fast
bsjp
swing
```

Mode `fast` dan `bsjp` menggunakan historical data:

```text
3 months
```

Sedangkan mode lainnya menggunakan:

```text
1 year
```

Hal ini dilakukan untuk mengurangi beban request dan mempercepat refresh data.

### Response

```json
{
    "chart": [
        {
            "time": "2026-09-23",
            "open": 4200,
            "high": 4300,
            "low": 4150,
            "close": 4250,
            "volume": 123456
        }
    ],
    "profile": {
        "nama": "PT Bank Rakyat Indonesia (Persero) Tbk",
        "sector": "Financial Services",
        "summary": "..."
    }
}
```

---

# 2. IDX Stock Ticker Filter

```http
GET /api/get_idx_tickers
```

Mengambil daftar ticker saham IDX berdasarkan rentang harga.

### Parameters

| Parameter | Required | Default | Description |
|---|---|---|---|
| `min` | No | `0` | Minimum harga |
| `max` | No | `9999999` | Maximum harga |

### Example

```text
/api/get_idx_tickers?min=1000&max=5000
```

### Response

```json
{
    "tickers": [
        "BBRI",
        "BMRI",
        "BBCA"
    ],
    "total": 3
}
```

---

# Ticker Data Source

Endpoint `/api/get_idx_tickers` menggunakan dua sumber data.

## Primary Source

GitHub Gist digunakan sebagai sumber utama daftar ticker.

Aplikasi akan melakukan request dengan timeout:

```text
5 seconds
```

Jika request berhasil dan menghasilkan data ticker, data tersebut digunakan.

## Fallback Source

Jika GitHub Gist:

- tidak dapat diakses
- timeout
- mengembalikan HTTP error
- menghasilkan data kosong

maka aplikasi akan menggunakan:

```text
DaftarSaham.xlsx
```

File Excel harus berada di folder yang sama dengan `server.py`.

Format Excel minimal harus memiliki kolom:

```text
Kode
```

Contoh:

| Kode |
|---|
| BBCA |
| BBRI |
| BMRI |
| TLKM |

---

# 3. US Stock

```http
GET /api/saham_us
```

Mengambil historical data saham Amerika Serikat.

### Parameters

| Parameter | Required | Description |
|---|---|---|
| `ticker` | Yes | Stock ticker |

### Example

```text
/api/saham_us?ticker=AAPL
```

Contoh ticker:

```text
AAPL
TSLA
NVDA
MSFT
AMZN
```

Data historical yang digunakan:

```text
1 year
```

### Response

```json
[
    {
        "time": "2026-09-23",
        "open": 150.0,
        "high": 155.0,
        "low": 149.0,
        "close": 153.0,
        "volume": 12345678
    }
]
```

---

# 4. Forex

```http
GET /api/forex
```

Mengambil historical data forex.

### Parameters

| Parameter | Required | Description |
|---|---|---|
| `pair` | Yes | Forex pair |

Aplikasi akan otomatis menambahkan:

```text
=X
```

jika belum diberikan.

### Example

```text
/api/forex?pair=EURUSD
```

Akan diproses menjadi:

```text
EURUSD=X
```

Contoh pair lainnya:

```text
USDJPY
GBPUSD
AUDUSD
EURUSD
USDCHF
```

Historical data:

```text
1 year
```

---

# Data Provider

Historical market data diperoleh menggunakan:

```text
yfinance
```

yang mengambil data dari Yahoo Finance.

Karena data berasal dari external service, API dapat mengalami:

- timeout
- request failure
- rate limiting
- data kosong
- temporary service issues

Jika error terjadi pada Yahoo Finance, coba request kembali beberapa saat kemudian.

---

# Troubleshooting

## `ModuleNotFoundError`

Contoh:

```text
ModuleNotFoundError: No module named 'flask'
```

Install seluruh dependency:

### Windows

```bash
py -m pip install -r requirements.txt
```

### Linux / macOS

```bash
python3 -m pip install -r requirements.txt
```

---

## Flask tidak ditemukan

```text
ModuleNotFoundError: No module named 'flask'
```

Install:

```bash
python -m pip install Flask
```

Windows juga dapat menggunakan:

```bash
py -m pip install Flask
```

---

## flask_cors tidak ditemukan

```text
ModuleNotFoundError: No module named 'flask_cors'
```

Install:

```bash
py -m pip install flask-cors
```

---

## yfinance tidak ditemukan

```text
ModuleNotFoundError: No module named 'yfinance'
```

Install:

```bash
py -m pip install yfinance
```

---

## pandas tidak ditemukan

```text
ModuleNotFoundError: No module named 'pandas'
```

Install:

```bash
py -m pip install pandas
```

---

## openpyxl tidak ditemukan

```text
ModuleNotFoundError: No module named 'openpyxl'
```

Install:

```bash
py -m pip install openpyxl
```

---

## requests tidak ditemukan

```text
ModuleNotFoundError: No module named 'requests'
```

Install:

```bash
py -m pip install requests
```

---

# Python dan pip Menggunakan Environment Berbeda

Salah satu masalah umum pada Windows adalah `pip` menginstall library ke Python yang berbeda dengan Python yang digunakan untuk menjalankan aplikasi.

Hindari:

```bash
pip install ...
```

Lebih aman menggunakan:

```bash
py -m pip install -r requirements.txt
```

Kemudian menjalankan:

```bash
py server.py
```

Linux/macOS:

```bash
python3 -m pip install -r requirements.txt
```

dan:

```bash
python3 server.py
```

Dengan cara ini, dependency diinstall ke environment Python yang sama.

---

# Excel Fallback Error

Jika muncul:

```text
Gist gagal dan file Excel Fallback tidak ditemukan di server!
```

Pastikan file:

```text
DaftarSaham.xlsx
```

berada di folder yang sama dengan:

```text
server.py
```

Struktur:

```text
stock-market-api/
├── server.py
├── requirements.txt
├── README.md
└── DaftarSaham.xlsx
```

Jika file tersedia tetapi muncul:

```text
Kolom 'Kode' tidak ditemukan
```

pastikan Excel memiliki kolom:

```text
Kode
```

---

# GitHub Gist Unavailable

Jika GitHub Gist tidak dapat diakses, aplikasi secara otomatis mencoba:

```text
DaftarSaham.xlsx
```

sebagai fallback.

Namun, data harga saham tetap membutuhkan koneksi ke Yahoo Finance melalui `yfinance`.

Jadi fallback Excel hanya menggantikan **sumber daftar ticker**, bukan sumber harga saham.

---

# Development

Server berjalan menggunakan Flask development server:

```python
app.run(debug=True, port=5000)
```

Default address:

```text
http://127.0.0.1:5000
```

Port:

```text
5000
```

---

# Notes

- API membutuhkan koneksi internet untuk mengambil market data.
- Data market tidak disimpan secara lokal.
- Historical data bergantung pada ketersediaan data dari Yahoo Finance.
- GitHub Gist digunakan sebagai sumber daftar ticker utama.
- `DaftarSaham.xlsx` digunakan sebagai fallback.
- Jangan mengandalkan API ini untuk data real-time atau keputusan transaksi tanpa melakukan validasi terhadap sumber data lain.

---

# License

```text
MIT License
```
