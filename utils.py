# utils.py
import requests
import database as db
from cache import produk_cache
from config import BASE_URL_AKRAB, API_KEY
def get_harga_produk(kode, api_produk=None):
    admin_data = db.get_produk_admin(kode)
    if admin_data and admin_data.get("harga", 0) > 0: return admin_data["harga"]
    if api_produk and "harga" in api_produk: return int(api_produk["harga"])
    try:
        for produk in produk_cache.get("data", []):
            if produk.get("type") == kode: return int(produk.get("harga", 0))
        url = f"{BASE_URL_AKRAB}/cek_stock_akrab?api_key={API_KEY}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers, timeout=10)
        data = res.json()
        for produk in data.get("data", []):
            if produk.get("type") == kode: return int(produk.get("harga", 0))
    except Exception: pass
    return 0
