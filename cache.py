# cache.py
import time, threading, requests
from config import logger, BASE_URL_AKRAB, API_KEY
produk_cache = {"data": [], "last_updated": 0, "update_in_progress": False}
def update_produk_cache_background():
    if produk_cache["update_in_progress"]: return
    produk_cache["update_in_progress"] = True
    try:
        start_time = time.time()
        url = f"{BASE_URL_AKRAB}/cek_stock_akrab?api_key={API_KEY}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
        data = res.json()
        if isinstance(data.get("data"), list):
            produk_cache["data"] = data["data"]
            produk_cache["last_updated"] = time.time()
            logger.info(f"Cache produk diperbarui: {len(data['data'])} produk. Waktu: {time.time() - start_time:.2f}s")
        else:
            logger.error("Format data stok tidak dikenali saat update cache.")
    except Exception as e:
        logger.error(f"Gagal memperbarui cache produk: {e}")
    finally:
        produk_cache["update_in_progress"] = False
