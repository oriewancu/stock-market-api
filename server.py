from flask import Flask, jsonify, request
from flask_cors import CORS
from tvDatafeed import TvDatafeed, Interval
from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd
import requests
import json
import os
import time
import traceback

app = Flask(__name__)
CORS(app)

# 1. Inisialisasi TradingView (Guest Mode)
print("Menginisialisasi TradingView...")
tv = TvDatafeed()
print("TradingView Siap!")

@app.route('/api/saham')
def get_saham():
    # Ambil parameter sumber data, default ke yfinance
    sumber_data = request.args.get('data', 'yfinance').lower()

    if sumber_data == 'yfinance':
        return get_saham_yfinance()
    elif sumber_data == 'goapi':
        return get_saham_goapi()
    elif sumber_data == 'marketstack':
        return get_saham_marketstack()
    else:
        return get_saham_tv()

def get_saham_marketstack():
    ticker_raw = request.args.get('ticker', 'BBRI').upper()
    # Hapus .JK bawaan YFinance
    ticker = ticker_raw.replace('.JK', '')
    gaya = request.args.get('gaya', 'swing').lower()
    
    # API Key Marketstack Anda
    MARKETSTACK_KEY = "YOUR_MARKETSTACK_KEY"
    
    # Marketstack menggunakan MIC code XIDX untuk Bursa Efek Indonesia
    symbol = f"{ticker}.XIDX"
    
    # Jumlah bar: 90 untuk Fast, 260 untuk Swing
    jumlah_bar = 90 if gaya in ['fast', 'bsjp'] else 260
    
    # Endpoint historical EOD Marketstack
    url = "https://api.marketstack.com/v1/eod"
    
    params = {
        'access_key': MARKETSTACK_KEY,
        'symbols': symbol,
        'limit': jumlah_bar
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code != 200:
            return jsonify({"error": f"Gagal dari Marketstack. HTTP: {response.status_code} - {response.text}"}), 400
            
        data_json = response.json()
        
        # Cek apakah ada data di dalam array 'data'
        results = data_json.get('data', [])
        
        if not results:
            return jsonify({"error": f"Data chart {ticker} kosong di Marketstack!"}), 400

        data_grafik = []
        for row in results:
            # Marketstack mereturn tanggal dengan format ISO: "2026-10-14T00:00:00+0000"
            # Kita potong 10 karakter pertama jadi YYYY-MM-DD
            raw_date = str(row.get('date', ''))[:10]
            
            data_grafik.append({
                "time": raw_date,
                "open": float(row.get('open', 0) or 0),
                "high": float(row.get('high', 0) or 0),
                "low": float(row.get('low', 0) or 0),
                "close": float(row.get('close', 0) or 0),
                "volume": int(row.get('volume', 0) or 0)
            })
        
        # Marketstack mereturn data Descending (Terbaru ke Terlama)
        # Kita sort menjadi Ascending agar library chart di frontend tidak error
        data_grafik = sorted(data_grafik, key=lambda x: x['time'])
            
        return jsonify({
            "chart": data_grafik,
            "profile": {
                "nama": ticker,
                "sector": "Bursa Efek Indonesia",
                "summary": "Data Historikal EOD disediakan oleh Marketstack."
            }
        })
        
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Koneksi ke Marketstack timeout/gagal: {str(e)}"}), 502
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Terjadi kesalahan internal Marketstack: {str(e)}"}), 500

def get_saham_goapi():
    # GoAPI menggunakan kode saham standar 4 huruf (tanpa .JK)
    ticker_raw = request.args.get('ticker', 'BBRI').upper()
    ticker = ticker_raw.replace('.JK', '')
    gaya = request.args.get('gaya', 'swing').lower()
    
    GOAPI_KEY = "YOUR_GOAPI_KEY"
    
    # Setup rentang waktu (sesuaikan dengan logic yfinance sebelumnya)
    # Fast/BSJP = ~3 bulan (90 hari)
    # Swing = ~1 tahun (365 hari)
    hari_mundur = 90 if gaya in ['fast', 'bsjp'] else 365
    
    end_date = datetime.now().strftime('%Y-%m-%d')
    start_date = (datetime.now() - timedelta(days=hari_mundur)).strftime('%Y-%m-%d')
    
    url_historical = f"https://api.goapi.io/stock/idx/{ticker}/historical"
    
    # 1. Sesuaikan Headers sesuai doc API
    headers = {
        'accept': 'application/json',
        'X-API-KEY': GOAPI_KEY
    }
    
    # 2. Sesuaikan parameter tanggal
    params = {
        'from': start_date,
        'to': end_date
    }
    
    try:
        # Request ke GoAPI
        response = requests.get(url_historical, headers=headers, params=params, timeout=10)
        
        if response.status_code != 200:
            return jsonify({"error": f"Gagal mengambil data dari GoAPI. HTTP Status: {response.status_code} - {response.text}"}), 400
            
        data_json = response.json()
        
        if data_json.get('status') != 'success' or 'data' not in data_json:
            return jsonify({"error": f"Data saham {ticker} tidak ditemukan di GoAPI!"}), 400
            
        # Ambil list data dari object JSON
        results = data_json['data'].get('results', data_json['data']) 
        
        if not results:
            return jsonify({"error": f"Data chart {ticker} kosong dari GoAPI untuk periode {start_date} s/d {end_date}!"}), 400

        data_grafik = []
        for row in results:
            # Pastikan tanggal terpotong jadi YYYY-MM-DD saja untuk amannya
            raw_date = str(row.get('date', ''))[:10]
            
            data_grafik.append({
                "time": raw_date,
                "open": float(row.get('open', 0)),
                "high": float(row.get('high', 0)),
                "low": float(row.get('low', 0)),
                "close": float(row.get('close', 0)),
                "volume": int(row.get('volume', 0))
            })
        
        # Sortir grafik dari data lama ke terbaru (Ascending) agar chart bisa render dengan benar
        data_grafik = sorted(data_grafik, key=lambda x: x['time'])
            
        return jsonify({
            "chart": data_grafik,
            "profile": {
                "nama": ticker,
                "sector": "Bursa Efek Indonesia",
                "summary": "Data Historikal disediakan oleh GoAPI-ID."
            }
        })
        
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Koneksi ke GoAPI timeout/gagal: {str(e)}"}), 502
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Terjadi kesalahan internal GoAPI: {str(e)}"}), 500

def get_saham_tv():
    # TradingView tidak memakai .JK, cukup nama ticker dan exchange IDX
    ticker_raw = request.args.get('ticker', 'BBRI').upper()
    ticker = ticker_raw.replace('.JK', '')
    gaya = request.args.get('gaya', 'swing').lower()

    try:
        # 60 bar untuk FAST/BSJP, 260 bar (1 tahun trading) untuk SWING
        limit_bars = 60 if gaya in ['fast', 'bsjp'] else 260
        
        df = None
        max_retries = 3
        
        # LOOP RETRY MAKSIMAL 3 KALI
        for attempt in range(max_retries):
            try:
                # Ambil data dari bursa IDX
                df = tv.get_hist(symbol=ticker, exchange='IDX', interval=Interval.in_daily, n_bars=limit_bars)
                
                # Jika data berhasil ditarik dan tidak kosong, langsung keluar dari loop
                if df is not None and not df.empty:
                    break
                
                print(f"[Warning] Percobaan {attempt + 1} gagal fetch {ticker} dari TradingView. Data kosong.")
                time.sleep(1) # Jeda 1 detik sebelum mencoba lagi
            except Exception as e:
                print(f"[Error] Percobaan {attempt + 1} gagal: {e}")
                if attempt == max_retries - 1:
                    # Jika sudah percobaan terakhir (ke-3) dan tetap error, lempar ke exception utama
                    raise e
                time.sleep(1) # Jeda sebelum retry jika ada exception
        
        # Cek hasil akhir setelah loop selesai
        if df is None or df.empty:
            return jsonify({"error": f"Data saham {ticker} tidak ditemukan di TradingView setelah {max_retries} kali percobaan!"}), 400
            
        # Bersihkan data jika ada baris kosong
        df = df.dropna(subset=['close'])
        if df.empty:
            return jsonify({"error": f"Data saham {ticker} kosong setelah dibersihkan!"}), 400

        data_grafik = []
        for index, row in df.iterrows():
            t_str = index.strftime('%Y-%m-%d')
            data_grafik.append({
                "time": t_str,
                "open": float(row['open']),
                "high": float(row['high']),
                "low": float(row['low']),
                "close": float(row['close']),
                "volume": int(row['volume'])
            })
            
        return jsonify({
            "chart": data_grafik,
            "profile": {
                "nama": ticker,
                "sector": "IDX Stock",
                "summary": "Data Real-time disediakan oleh TradingView."
            }
        })
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": f"Gagal fetch data TradingView: {str(e)}"}), 500

def get_saham_yfinance():
    ticker = request.args.get('ticker', 'BBRI').upper()
    gaya = request.args.get('gaya', 'swing').lower()
    
    if not ticker.endswith('.JK'):
        ticker += '.JK'
        
    try:
        saham = yf.Ticker(ticker)
        
        # OPTIMASI KECEPATAN (AUTO-REFRESH FRIENDLY)
        if gaya in ['fast', 'bsjp']:
            df = saham.history(period="3mo", interval="1d")
        else:
            df = saham.history(period="1y", interval="1d")
        
        if df.empty:
            return jsonify({"error": f"Data saham {ticker} tidak ditemukan!"}), 400
            
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
    
    gist_url = "https://gist.githubusercontent.com/oriewancu/113e249ccfbbd4f62d27c71aa751269f/raw/847ba68dd97c4bc079192c1b892cc94255ef904c/saham.json" 
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    excel_file = os.path.join(BASE_DIR, "DaftarSaham.xlsx")
    
    list_emiten = []
    
    try:
        req = requests.get(gist_url, timeout=5)
        if req.status_code == 200:
            list_emiten = json.loads(req.text)
            print("Berhasil mengambil data emiten dari Gist.")
        else:
            print(f"Gist mengembalikan status {req.status_code}. Beralih ke fallback.")
    except Exception as e:
        print(f"Gagal mengambil dari Gist: {e}. Beralih ke fallback.")
    
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

    list_emiten = [str(t).upper().strip() for t in list_emiten if len(str(t).strip()) == 4 and str(t).strip().isalpha()]
    
    if not list_emiten:
        return jsonify({"error": "Daftar emiten kosong setelah dibersihkan."}), 400

    try:
        # TETAP GUNAKAN YFINANCE UNTUK FILTER HARGA AWAL SECARA MASSAL AGAR CEPAT
        tickers_str = " ".join([t + ".JK" for t in list_emiten])
        df_yf = yf.download(tickers_str, period="1d", progress=False)
        hasil = []
        
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


if __name__ == '__main__':
    app.run(debug=True, port=5000)