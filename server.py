"""
============================================================
STOCK API SERVER
============================================================

REQUIREMENTS
------------
Python 3.10+ disarankan.

Python libraries:
    Flask
    flask-cors
    yfinance
    pandas
    openpyxl

Cara install dependency:

Linux / macOS:
    python3 -m pip install -r requirements.txt

Windows:
    py -m pip install -r requirements.txt

Jika pip belum tersedia:

Windows:
    py -m ensurepip --upgrade
    py -m pip install --upgrade pip

Linux / macOS:
    python3 -m ensurepip --upgrade
    python3 -m pip install --upgrade pip


FIRST RUN
---------
1. Pastikan Python sudah terinstall.
2. Buka terminal / CMD di folder project.
3. Install dependency:

       Windows:
       py -m pip install -r requirements.txt

       Linux/macOS:
       python3 -m pip install -r requirements.txt

4. Pastikan file berikut berada dalam folder yang sama:
       server.py
       requirements.txt
       Daftar Saham  - 20260924.xlsx

5. Jalankan server:

       Windows:
       py server.py

       Linux/macOS:
       python3 server.py

6. Server akan berjalan di:
       http://127.0.0.1:5000


TROUBLESHOOTING
---------------
Jika pip menggunakan Python yang berbeda dengan Python
yang menjalankan server, gunakan:

    Windows:
        py -m pip install -r requirements.txt
        py server.py

    Linux/macOS:
        python3 -m pip install -r requirements.txt
        python3 server.py

============================================================
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import yfinance as yf
import pandas as pd
import requests
import json
import os
import traceback

app = Flask(__name__)
CORS(app)

@app.route('/api/saham')
def get_saham():
    ticker = request.args.get('ticker', 'BBRI').upper()
    gaya = request.args.get('gaya', 'swing').lower() # Tangkap parameter gaya bermain
    
    if not ticker.endswith('.JK'):
        ticker += '.JK'
        
    try:
        saham = yf.Ticker(ticker)
        
        # OPTIMASI KECEPATAN (AUTO-REFRESH FRIENDLY)
        # Kurangi beban load data berdasarkan gaya bermain
        if gaya in ['fast', 'bsjp']:
            # MA maksimal yang dihitung frontend adalah MA15 & 20 hari (untuk tren bulanan)
            # period "3mo" (3 bulan) sudah sangat aman, load data jadi super kilat
            df = saham.history(period="3mo", interval="1d")
        else:
            # Mode swing menghitung MA50, jadi butuh data 6 bulan atau 1 tahun
            df = saham.history(period="1y", interval="1d")
        
        if df.empty:
            return jsonify({"error": f"Data saham {ticker} tidak ditemukan!"}), 400
            
        # Ambil info profil singkat dari yfinance
        # (Catatan: Jika kedepannya API sering timeout, bagian .info ini bisa dibuat caching)
        info = saham.info
        nama_pt = info.get('longName', ticker)
        sektor = info.get('sector', 'Sektor Tidak Diketahui')
        deskripsi = info.get('longBusinessSummary', 'Deskripsi profil belum tersedia.')

        data_grafik = []
        for index_str, row in df.iterrows():
            t_str = index_str.strftime('%Y-%m-%d')
            data_grafik.append({
                "time": t_str,
                "open": float(row['Open']),
                "high": float(row['High']),
                "low": float(row['Low']),
                "close": float(row['Close']),
                "volume": int(row['Volume'])
            })
            
        # Kirim data chart beserta profil perusahaannya
        return jsonify({
            "chart": data_grafik,
            "profile": {
                "nama": nama_pt,
                "sector": sektor,
                "summary": deskripsi
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/get_idx_tickers', methods=['GET'])
def get_idx_tickers():
    min_harga = float(request.args.get('min', 0))
    max_harga = float(request.args.get('max', 9999999))
    
    # 1. Konfigurasi URL Gist dan nama file Excel Fallback
    gist_url = "https://gist.githubusercontent.com/oriewancu/113e249ccfbbd4f62d27c71aa751269f/raw/847ba68dd97c4bc079192c1b892cc94255ef904c/saham.json" 

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    excel_file = os.path.join(BASE_DIR, "DaftarSaham.xlsx")
    
    list_emiten = []
    
    # 2. Coba Mengambil Data dari Gist (Utama)
    try:
        req = requests.get(gist_url, timeout=5) # Set timeout agar tidak menunggu terlalu lama jika GitHub down
        if req.status_code == 200:
            # Karena format Gist sekarang JSON Array ["MGLV", "TRUE", ...], gunakan json.loads
            list_emiten = json.loads(req.text)
            print("Berhasil mengambil data emiten dari Gist.")
        else:
            print(f"Gist mengembalikan status {req.status_code}. Beralih ke fallback.")
    except Exception as e:
        print(f"Gagal mengambil dari Gist: {e}. Beralih ke fallback.")
    
    # 3. Fallback ke Excel jika Gist gagal atau kosong
    if not list_emiten:
        try:
            if not os.path.exists(excel_file):
                return jsonify({"error": "Gist gagal dan file Excel Fallback tidak ditemukan di server!"}), 404
            
            df_excel = pd.read_excel(excel_file, engine='openpyxl')
            if 'Kode' in df_excel.columns:
                list_emiten = df_excel['Kode'].dropna().astype(str).str.strip().tolist()
                print("Berhasil menggunakan data emiten dari Excel (Fallback).")
            else:
                return jsonify({"error": "Format Excel Fallback salah. Kolom 'Kode' tidak ditemukan."}), 400
        except Exception as e:
            return jsonify({"error": f"Gist gagal dan pemrosesan Excel Fallback error: {e}"}), 500

    # 4. Validasi dan Pembersihan Format Kode Emiten
    # Pastikan hanya string dengan 4 huruf (membuang spasi kosong atau data sampah)
    list_emiten = [str(t).upper().strip() for t in list_emiten if len(str(t).strip()) == 4 and str(t).strip().isalpha()]
    
    if not list_emiten:
        return jsonify({"error": "Daftar emiten kosong setelah dibersihkan."}), 400

    # 5. Download Harga Secara Massal melalui yfinance
    try:
        tickers_str = " ".join([t + ".JK" for t in list_emiten])
        df_yf = yf.download(tickers_str, period="1d", progress=False)
        hasil = []
        
        # 6. Filter Berdasarkan Rentang Harga Input Pengguna
        if 'Close' in df_yf:
            df_close = df_yf['Close']
            
            for t in list_emiten:
                t_jk = t + ".JK"
                if t_jk in df_close:
                    saham_data = df_close[t_jk].dropna()
                    
                    if not saham_data.empty:
                        harga_terakhir = float(saham_data.iloc[-1])
                        
                        if min_harga <= harga_terakhir <= max_harga:
                            hasil.append(t)
                            
        return jsonify({"tickers": hasil, "total": len(hasil)})
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/api/saham_us', methods=['GET'])
def get_saham_us():
    ticker_symbol = request.args.get('ticker')
    if not ticker_symbol:
        return jsonify({"error": "Ticker tidak boleh kosong"}), 400
    
    # Saham AS tidak perlu ditambah .JK
    ticker = ticker_symbol.upper() 
    
    try:
        saham = yf.Ticker(ticker)
        # Ambil data 1 tahun ke belakang agar perhitungan MA50 dan Timeframe aman
        df = saham.history(period="1y") 
        
        if df.empty:
            return jsonify({"error": f"Data saham {ticker} tidak ditemukan!"}), 404
            
        data_grafik = []
        for index, row in df.iterrows():
            data_grafik.append({
                "time": index.strftime('%Y-%m-%d'),
                "open": float(row['Open']),
                "high": float(row['High']),
                "low": float(row['Low']),
                "close": float(row['Close']),
                "volume": int(row['Volume'])
            })
            
        return jsonify(data_grafik)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/forex', methods=['GET'])
def get_forex():
    pair_symbol = request.args.get('pair')
    if not pair_symbol:
        return jsonify({"error": "Pair tidak boleh kosong"}), 400
    
    # Format forex di yfinance wajib menggunakan akhiran =X (Cth: EURUSD=X)
    ticker = pair_symbol.upper().strip()
    if not ticker.endswith('=X'):
        ticker += '=X'
    
    try:
        forex_data = yf.Ticker(ticker)
        df = forex_data.history(period="1y")
        
        if df.empty:
            return jsonify({"error": f"Data pair {ticker} tidak ditemukan!"}), 404
            
        data_grafik = []
        for index, row in df.iterrows():
            data_grafik.append({
                "time": index.strftime('%Y-%m-%d'),
                "open": float(row['Open']),
                "high": float(row['High']),
                "low": float(row['Low']),
                "close": float(row['Close']),
                "volume": int(row['Volume'])
            })
            
        return jsonify(data_grafik)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("🚀 Server berjalan di http://127.0.0.1:5000")
    app.run(debug=True, port=5000)
