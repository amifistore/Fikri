# ui.py
import time, threading, requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from config import logger, ADMIN_IDS, BASE_URL_AKRAB, CACHE_DURATION, API_KEY
import database as db
from cache import produk_cache, update_produk_cache_background
from utils import get_harga_produk
async def generate_main_keyboard():
    static_layout = [['All Bekasan (stok: ?)'],['Cek Area', 'Cek Dompul'],['Cek Saldo'],['Cek Stock Fresh', 'Cek Stock Bekasan'],['Unreg Mandiri'],['Topup Saldo']]
    product_buttons = []
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        url = f"{BASE_URL_AKRAB}/cek_stock_akrab?api_key={API_KEY}"
        res = requests.get(url, headers=headers, timeout=10)
        res.raise_for_status()
        api_data = res.json().get('data', [])
        stock_dict = {item['nama'].strip(): int(item.get('sisa_slot', 0)) for item in api_data}
        product_layout_names = [['SuperMini', 'Mini'], ['Big', 'Jumbo V2'], ['JUMBO', 'MegaBig']]
        for row_names in product_layout_names:
            button_row = [f"{name} (stok: {stock_dict.get(name, 0)})" for name in row_names]
            product_buttons.append(button_row)
    except Exception as e:
        logger.error(f"Gagal mengambil stok untuk keyboard utama: {e}")
        product_buttons = [['Gagal memuat produk']]
    full_layout = static_layout[:4] + product_buttons + static_layout[4:]
    return ReplyKeyboardMarkup(full_layout, resize_keyboard=True, one_time_keyboard=False)
def btn_kembali(): return [InlineKeyboardButton("🔙 Kembali", callback_data="main_menu_inline")]
def get_menu(uid): return menu_admin(uid) if uid in ADMIN_IDS else menu_user(uid)
def btn_kembali_menu(): return [InlineKeyboardButton("🏠 Menu Utama", callback_data="main_menu_inline")]
def menu_user(uid): return InlineKeyboardMarkup([ [InlineKeyboardButton("🛒 Beli Produk", callback_data='beli_produk'), InlineKeyboardButton("💳 Top Up Saldo", callback_data='topup_menu')], [InlineKeyboardButton("📋 Riwayat Transaksi", callback_data='riwayat'), InlineKeyboardButton("📦 Info Stok", callback_data='cek_stok')], [InlineKeyboardButton("🧾 Riwayat Top Up", callback_data="topup_riwayat"), InlineKeyboardButton("🔑 Kode Unik Saya", callback_data="my_kode_unik")], [InlineKeyboardButton("ℹ️ Bantuan", callback_data="bantuan")]])
def menu_admin(uid): return InlineKeyboardMarkup([ [InlineKeyboardButton("🛒 Beli Produk", callback_data='beli_produk'), InlineKeyboardButton("💳 Top Up Saldo", callback_data='topup_menu')], [InlineKeyboardButton("📋 Riwayat Saya", callback_data='riwayat'), InlineKeyboardButton("📦 Info Stok", callback_data='cek_stok')], [InlineKeyboardButton("👥 Admin Panel", callback_data='admin_panel')], [InlineKeyboardButton("ℹ️ Bantuan", callback_data="bantuan")]])
def admin_panel_menu(): return InlineKeyboardMarkup([ [InlineKeyboardButton("👤 Data User", callback_data='admin_cekuser'), InlineKeyboardButton("💰 Lihat Saldo", callback_data='lihat_saldo')], [InlineKeyboardButton("📊 Semua Riwayat", callback_data='semua_riwayat'), InlineKeyboardButton("📢 Broadcast", callback_data='broadcast')], [InlineKeyboardButton("✅ Approve Top Up", callback_data="admin_topup_pending"), InlineKeyboardButton("⚙️ Manajemen Produk", callback_data="admin_produk")], [InlineKeyboardButton("🔑 Generate Kode Unik", callback_data="admin_generate_kode")], [InlineKeyboardButton("🔙 Kembali", callback_data="main_menu_inline")]])
def topup_menu_buttons(): return InlineKeyboardMarkup([ [InlineKeyboardButton("💳 QRIS (Otomatis)", callback_data="topup_qris")], [InlineKeyboardButton("🔑 Kode Unik (Manual)", callback_data="topup_kode_unik")], [InlineKeyboardButton("🔙 Kembali", callback_data="main_menu_inline")]])
def dashboard_msg(user): return f"✨ <b>DASHBOARD USER</b> ✨\n\n👤 <b>{user.full_name}</b>\n📧 @{user.username or '-'}\n🆔 <code>{user.id}</code>\n\n💰 <b>Saldo:</b> <code>Rp {db.get_saldo(user.id):,}</code>\n📊 <b>Total Transaksi:</b> <b>{db.get_riwayat_jml(user.id)}</b>\n"
def produk_inline_keyboard(is_admin=False):
    try:
        current_time = time.time()
        if current_time - produk_cache["last_updated"] > CACHE_DURATION:
            thread = threading.Thread(target=update_produk_cache_background)
            thread.daemon = True
            thread.start()
        data = {"data": produk_cache["data"]} if produk_cache["data"] else None
        if not data:
            url = f"{BASE_URL_AKRAB}/cek_stock_akrab?api_key={API_KEY}"
            headers = {'User-Agent': 'Mozilla/5.0'}
            res = requests.get(url, headers=headers, timeout=10)
            data = res.json()
            if isinstance(data.get("data"), list):
                produk_cache["data"] = data["data"]
                produk_cache["last_updated"] = current_time
        keyboard = []
        api_produk_list = data.get("data", [])
        if api_produk_list:
            for produk in api_produk_list:
                kode, nama, slot = produk['type'], produk['nama'], int(produk.get('sisa_slot', 0))
                harga = get_harga_produk(kode, produk)
                status = "✅" if slot > 0 else "❌"
                callback_data = f"produk|{kode}|{nama}" if slot > 0 else "disabled_produk"
                label = f"{status} [{kode}] {nama} | Rp{harga:,}"
                if is_admin: keyboard.append([InlineKeyboardButton(label, callback_data=f"admin_produk_detail|{kode}")])
                else: keyboard.append([InlineKeyboardButton(label, callback_data=callback_data)])
        if not keyboard: keyboard.append([InlineKeyboardButton("❌ Tidak ada produk tersedia", callback_data="disabled_produk")])
        keyboard.append([InlineKeyboardButton("🔙 Kembali", callback_data="main_menu_inline")])
        return InlineKeyboardMarkup(keyboard)
    except Exception as e:
        logger.error(f"Error loading products for inline keyboard: {e}")
        return InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Ulangi", callback_data="beli_produk")], [InlineKeyboardButton("🔙 Kembali", callback_data="main_menu_inline")]])
