# handlers/product.py
import uuid
from datetime import datetime
import httpx
from telegram import Update, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import CallbackContext, ConversationHandler
from constants import CHOOSING_PRODUK, INPUT_TUJUAN, KONFIRMASI
import database as db
import ui
from config import logger, BASE_URL, API_KEY
async def cek_stok_menu(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    try:
        url = f"{ui.BASE_URL_AKRAB}/cek_stock_akrab?api_key={API_KEY}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        async with httpx.AsyncClient() as client:
            res = await client.get(url, headers=headers, timeout=10)
            res.raise_for_status()
            data = res.json()
        data_to_show = data.get("data", [])
        msg = "📦 <b>Info Stok Akrab XL/Axis</b>\n\n"
        if isinstance(data_to_show, list) and data_to_show:
            for produk in data_to_show:
                status = "✅" if int(produk.get('sisa_slot', 0)) > 0 else "❌"
                msg += f"{status} <b>[{produk.get('type', 'N/A')}]</b> {produk.get('nama', 'N/A')}: {produk.get('sisa_slot', 0)} unit\n"
        else: msg += "❌ Gagal memuat data stok atau stok kosong."
    except Exception as e: msg = f"❌ Gagal mengambil data stok: {e}"
    await query.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([ui.btn_kembali()]))
    return ConversationHandler.END
async def beli_produk_menu(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("🔄 Memuat daftar produk...", reply_markup=InlineKeyboardMarkup([ui.btn_kembali()]))
    keyboard = ui.produk_inline_keyboard()
    await query.edit_message_text("🛒 <b>PILIH PRODUK</b>\n\nPilih produk yang ingin dibeli:", parse_mode=ParseMode.HTML, reply_markup=keyboard)
    return CHOOSING_PRODUK
async def pilih_produk_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    data = query.data
    await query.answer()
    if data.startswith("produk|"):
        try:
            _, kode, nama = data.split("|")
            harga = ui.get_harga_produk(kode)
            context.user_data["produk"] = {"kode": kode, "nama": nama, "harga": harga}
            admin_data = db.get_produk_admin(kode)
            deskripsi = admin_data["deskripsi"] if admin_data and admin_data["deskripsi"] else ""
            desc_show = f"\n📝 <b>Deskripsi:</b>\n<code>{deskripsi}</code>\n" if deskripsi else ""
            await query.edit_message_text(f"✅ <b>Produk Dipilih:</b>\n\n📦 <b>[{kode}] {nama}</b>\n💰 <b>Harga:</b> Rp {harga:,}\n{desc_show}\n📱 <b>Masukkan nomor tujuan:", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([ui.btn_kembali()]))
            return INPUT_TUJUAN
        except Exception as e:
            logger.error(f"Error in pilih_produk_callback: {e}")
            await query.edit_message_text("❌ Terjadi kesalahan.", reply_markup=InlineKeyboardMarkup([ui.btn_kembali()]))
    elif data == "disabled_produk": await query.answer("⚠️ Produk ini sedang habis!", show_alert=True)
    return ConversationHandler.END
async def input_tujuan_step(update: Update, context: CallbackContext):
    tujuan = update.message.text.strip()
    if not tujuan.isdigit() or len(tujuan) < 8:
        await update.message.reply_text("❌ Nomor tidak valid, masukkan ulang:", reply_markup=InlineKeyboardMarkup([ui.btn_kembali()]))
        return INPUT_TUJUAN
    context.user_data["tujuan"] = tujuan
    produk = context.user_data["produk"]
    admin_data = db.get_produk_admin(produk["kode"])
    deskripsi = admin_data["deskripsi"] if admin_data and admin_data["deskripsi"] else ""
    desc_show = f"\n📝 <b>Deskripsi:</b>\n<code>{deskripsi}</code>\n" if deskripsi else ""
    await update.message.reply_text(f"✅ <b>KONFIRMASI PEMESANAN</b>\n\n📦 <b>Produk:</b> [{produk['kode']}] {produk['nama']}\n💰 <b>Harga:</b> Rp {produk['harga']:,}\n📱 <b>Nomor Tujuan:</b> <code>{tujuan}</code>\n{desc_show}\n⚠️ <b>Ketik 'YA' untuk konfirmasi atau 'BATAL' untuk membatalkan.", parse_mode=ParseMode.HTML)
    return KONFIRMASI
async def konfirmasi_step(update: Update, context: CallbackContext):
    text = update.message.text.strip().upper()
    if text == "BATAL":
        await update.message.reply_text("❌ Transaksi dibatalkan.", reply_markup=ui.get_menu(update.effective_user.id))
        return ConversationHandler.END
    if text != "YA":
        await update.message.reply_text("❌ Ketik 'YA' atau 'BATAL'.", reply_markup=InlineKeyboardMarkup([ui.btn_kembali()]))
        return KONFIRMASI
    produk, tujuan, user, harga = context.user_data["produk"], context.user_data["tujuan"], update.effective_user, context.user_data["produk"].get("harga", 0)
    if db.get_saldo(user.id) < harga:
        await update.message.reply_text("❌ Saldo Anda tidak cukup.", reply_markup=ui.get_menu(user.id))
        return ConversationHandler.END
    reffid = str(uuid.uuid4())
    url = f"{BASE_URL}/trx?produk={produk['kode']}&tujuan={tujuan}&reff_id={reffid}&api_key={API_KEY}"
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        async with httpx.AsyncClient() as client:
            res = await client.get(url, headers=headers, timeout=15)
            res.raise_for_status()
            data = res.json()
        status_text, keterangan = data.get('status', 'PENDING'), data.get('message', 'Transaksi sedang diproses.')
    except Exception as e:
        logger.error(f"Gagal request ke provider: {e}")
        await update.message.reply_text(f"❌ Gagal menghubungi provider. Silakan coba lagi nanti.", reply_markup=ui.get_menu(user.id))
        return ConversationHandler.END
    db.log_riwayat(reffid, user.id, produk["kode"], tujuan, harga, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), status_text, keterangan)
    await update.message.reply_text(f"⏳ <b>TRANSAKSI SEDANG DIPROSES</b>\n\nPesanan Anda telah kami teruskan ke provider. Saldo akan dipotong setelah sukses.\n\n📦 <b>Produk:</b> [{produk['kode']}]\n📱 <b>Tujuan:</b> {tujuan}\n🔖 <b>RefID:</b> <code>{reffid}</code>", parse_mode=ParseMode.HTML, reply_markup=ui.get_menu(user.id))
    return ConversationHandler.END
