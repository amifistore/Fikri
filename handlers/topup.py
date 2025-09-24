# handlers/topup.py
import uuid, base64, random
from datetime import datetime
import httpx
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ParseMode
from telegram.ext import CallbackContext, ConversationHandler
from constants import TOPUP_AMOUNT, TOPUP_UPLOAD, INPUT_KODE_UNIK
import database as db
import ui
from config import logger, QRIS_STATIS, ADMIN_IDS
async def topup_menu(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("💳 <b>TOP UP SALDO</b>\nPilih metode top up:", parse_mode=ParseMode.HTML, reply_markup=ui.topup_menu_buttons())
    return TOPUP_AMOUNT
async def topup_qris_amount(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("💰 <b>TOP UP VIA QRIS</b>\n\nMasukkan nominal (contoh: 50000):", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([ui.btn_kembali()]))
    context.user_data['topup_method'] = 'qris'
    return TOPUP_AMOUNT
async def topup_kode_unik_menu(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("🔑 <b>TOP UP VIA KODE UNIK</b>\n\nMasukkan kode unik dari admin:", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([ui.btn_kembali()]))
    context.user_data['topup_method'] = 'kode_unik'
    return INPUT_KODE_UNIK
async def input_kode_unik_step(update: Update, context: CallbackContext):
    kode, user = update.message.text.strip(), update.effective_user
    kode_data = db.get_kode_unik(kode)
    if not kode_data or kode_data["digunakan"]:
        await update.message.reply_text("❌ Kode unik tidak valid atau sudah digunakan.", reply_markup=InlineKeyboardMarkup([ui.btn_kembali()]))
        return INPUT_KODE_UNIK
    db.tambah_saldo(user.id, kode_data["nominal"])
    db.gunakan_kode_unik(kode)
    await update.message.reply_text(f"✅ <b>TOP UP BERHASIL</b>\n\nNominal: <b>Rp {kode_data['nominal']:,}</b>\nSaldo sekarang: <b>Rp {db.get_saldo(user.id):,}</b>", parse_mode=ParseMode.HTML, reply_markup=ui.get_menu(user.id))
    return ConversationHandler.END
async def generate_qris(amount, qris_statis):
    url = "https://qrisku.my.id/api"
    payload, headers = {"amount": str(amount), "qris_statis": qris_statis}, {'User-Agent': 'Mozilla/5.0'}
    try:
        async with httpx.AsyncClient() as client:
            res = await client.post(url, json=payload, headers=headers, timeout=20)
            logger.info(f"QRIS API Response: {res.text}")
            res.raise_for_status()
            data = res.json()
        return (True, data['qris_base64']) if data.get('status') == 'success' and 'qris_base64' in data else (False, data.get('message', 'Gagal generate QRIS'))
    except Exception as e:
        logger.error(f"Error koneksi API QRIS: {e}")
        return False, str(e)
async def topup_amount_step(update: Update, context: CallbackContext):
    try:
        nominal = int(update.message.text.replace(".", "").replace(",", ""))
        if not (10000 <= nominal <= 5000000 and nominal % 1000 == 0): raise ValueError
    except ValueError:
        await update.message.reply_text("❌ Nominal kelipatan 1.000, min 10.000, max 5.000.000.", reply_markup=InlineKeyboardMarkup([ui.btn_kembali()]))
        return TOPUP_AMOUNT
    user, unique_code = update.effective_user, random.randint(100, 999)
    final_nominal = nominal + unique_code
    await update.message.reply_text("⏳ Sedang membuat kode QRIS, mohon tunggu...")
    sukses, hasil = await generate_qris(final_nominal, QRIS_STATIS)
    if sukses:
        try:
            img_bytes = base64.b64decode(hasil)
            topup_id = str(uuid.uuid4())
            db.insert_topup_pending(topup_id, user.id, user.username or "", user.full_name, final_nominal, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "pending")
            for adm in ADMIN_IDS:
                try: await context.bot.send_message(adm, f"🔔 Permintaan top up QRIS baru!\nUser: <b>{user.full_name}</b> (@{user.username or '-'})\nNominal: <b>Rp {final_nominal:,}</b>", parse_mode=ParseMode.HTML)
                except Exception as e: logger.error(f"Notif admin gagal: {e}")
            await update.message.reply_photo(photo=img_bytes, caption=f"💰 <b>QRIS UNTUK TOP UP</b>\n\nNominal: <b>Rp {final_nominal:,}</b>\nKode unik: <b>{unique_code}</b>\n\nScan QRIS di atas, lalu klik tombol di bawah untuk upload bukti.", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("📤 Upload Bukti", callback_data=f"topup_upload|{topup_id}")], ui.btn_kembali()]))
        except Exception as e:
            logger.error(f"Error QRIS (gagal decode): {e}")
            await update.message.reply_text(f"❌ Gagal memproses gambar QRIS. Respons dari API:\n\n<code>{hasil}</code>", parse_mode=ParseMode.HTML, reply_markup=ui.get_menu(user.id))
    else: await update.message.reply_text(f"❌ Gagal membuat QRIS dari provider. Pesan: {hasil}", reply_markup=ui.get_menu(user.id))
    return ConversationHandler.END
async def topup_upload_router(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    try:
        _, topup_id = query.data.split("|")
        context.user_data['topup_upload_id'] = topup_id
        await query.edit_message_text("📤 <b>UPLOAD BUKTI TRANSFER</b>\n\nKirimkan screenshot bukti transfer Anda:", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([ui.btn_kembali()]))
        return TOPUP_UPLOAD
    except Exception as e:
        logger.error(f"Error in topup_upload_router: {e}")
        await query.edit_message_text("❌ Terjadi kesalahan.", reply_markup=InlineKeyboardMarkup([ui.btn_kembali()]))
        return ConversationHandler.END
async def topup_upload_step(update: Update, context: CallbackContext):
    user, topup_id = update.effective_user, context.user_data.get('topup_upload_id')
    if not topup_id or not update.message.photo:
        await update.message.reply_text("❌ File yang dikirim bukan foto. Silakan upload ulang.", reply_markup=ui.get_menu(user.id))
        return ConversationHandler.END
    file_id, caption = update.message.photo[-1].file_id, update.message.caption or ""
    db.update_topup_bukti(topup_id, file_id, caption)
    for adm in ADMIN_IDS:
        try: await context.bot.send_message(adm, f"🔔 Bukti transfer baru masuk dari <b>{user.full_name}</b> untuk top up ID <code>{topup_id}</code>.", parse_mode=ParseMode.HTML)
        except Exception as e: logger.error(f"Notif admin gagal: {e}")
    context.user_data['topup_upload_id'] = None
    await update.message.reply_text("✅ Bukti transfer berhasil dikirim. Mohon tunggu admin verifikasi.", reply_markup=ui.get_menu(user.id))
    return ConversationHandler.END
async def topup_riwayat_menu(update: Update, context: CallbackContext):
    query, user = update.callback_query, update.effective_user
    await query.answer()
    items = db.get_topup_pending_by_user(user.id, 10)
    msg = "📋 <b>RIWAYAT TOP UP ANDA</b>\n\n"
    if not items: msg += "Belum ada permintaan top up."
    else:
        for r in items: msg += f"{'⏳' if r[6]=='pending' else ('✅' if r[6]=='approved' else '❌')} <b>{r[5]}</b>\nID: <code>{r[0]}</code>\nNominal: Rp {r[4]:,}\nStatus: <b>{r[6].capitalize()}</b>\n\n"
    await query.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([ui.btn_kembali()]))
    return ConversationHandler.END
async def my_kode_unik_menu(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    items = db.get_kode_unik_user(query.from_user.id)
    msg = "🔑 <b>KODE UNIK SAYA</b>\n\n"
    if not items: msg += "Belum ada kode unik yang dibuat."
    else:
        for kode in items: msg += f"Kode: <code>{kode['kode']}</code>\nNominal: Rp {kode['nominal']:,}\nStatus: {'✅ Digunakan' if kode['digunakan'] else '⏳ Belum digunakan'}\nDibuat: {kode['dibuat_pada']}\n\n"
    await query.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([ui.btn_kembali()]))
    return ConversationHandler.END
