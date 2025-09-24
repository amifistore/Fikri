# handlers/admin.py
from telegram import Update, InlineKeyboardMarkup, InputMediaPhoto
from telegram.constants import ParseMode
from telegram.ext import CallbackContext, ConversationHandler
from constants import BC_MESSAGE, ADMIN_CEKUSER, ADMIN_EDIT_HARGA, ADMIN_EDIT_DESKRIPSI, INPUT_KODE_UNIK
import database as db
import ui
from config import logger
async def admin_panel(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("⚙️ <b>ADMIN PANEL</b>\nPilih menu admin:", parse_mode=ParseMode.HTML, reply_markup=ui.admin_panel_menu())
    return ConversationHandler.END
async def admin_produk_menu(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("⚙️ <b>MANAJEMEN PRODUK</b>\nEdit harga/deskripsi produk:", parse_mode=ParseMode.HTML, reply_markup=ui.produk_inline_keyboard(is_admin=True))
    return ADMIN_CEKUSER
async def admin_produk_detail(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    kode = query.data.split("|")[1]
    produk_api = next((p for p in ui.produk_cache["data"] if p["type"] == kode), None)
    admin_data = db.get_produk_admin(kode)
    harga_bot = (admin_data and admin_data["harga"]) or (produk_api and int(produk_api.get("harga", 0))) or 0
    deskripsi_bot = (admin_data and admin_data["deskripsi"]) or ""
    msg = f"📦 <b>DETAIL PRODUK</b>\n\n<b>Kode:</b> {kode}\n"
    if produk_api: msg += f"<b>Nama:</b> {produk_api['nama']}\n<b>Stok:</b> {produk_api.get('sisa_slot', 0)}\n<b>Harga API:</b> Rp{int(produk_api.get('harga', 0)):,}\n"
    else: msg += "<b>Nama:</b> Produk tidak ditemukan di API\n"
    msg += f"<b>Harga Bot:</b> Rp{harga_bot:,}\n<b>Deskripsi:</b>\n<code>{deskripsi_bot or 'Tidak ada'}</code>"
    keyboard = [[InlineKeyboardButton("✏️ Edit Harga", callback_data=f"admin_edit_harga|{kode}"), InlineKeyboardButton("📝 Edit Deskripsi", callback_data=f"admin_edit_deskripsi|{kode}")], [InlineKeyboardButton("🔙 Kembali", callback_data="admin_produk")]]
    await query.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))
    return ADMIN_CEKUSER
async def admin_edit_harga(update: Update, context: CallbackContext):
    query, kode = update.callback_query, query.data.split("|")[1]
    await query.answer()
    context.user_data["admin_edit_kode"] = kode
    admin_data = db.get_produk_admin(kode)
    harga_sekarang = (admin_data and admin_data["harga"]) or 0
    await query.edit_message_text(f"💰 <b>EDIT HARGA</b>\nKode: <b>{kode}</b>\nHarga saat ini: <b>Rp {harga_sekarang:,}</b>\n\nMasukkan harga baru:", parse_mode=ParseMode.HTML)
    return ADMIN_EDIT_HARGA
async def admin_edit_harga_step(update: Update, context: CallbackContext):
    kode = context.user_data.get("admin_edit_kode")
    try:
        harga = int(update.message.text.replace(".", "").replace(",", ""))
        if harga <= 0: raise ValueError
        db.set_produk_admin_harga(kode, harga)
        await update.message.reply_text(f"✅ Harga untuk <b>{kode}</b> berhasil diupdate menjadi <b>Rp {harga:,}</b>.", parse_mode=ParseMode.HTML, reply_markup=ui.get_menu(update.effective_user.id))
        return ConversationHandler.END
    except (ValueError, TypeError):
        await update.message.reply_text("❌ Input harga salah. Masukkan angka lebih dari 0.")
        return ADMIN_EDIT_HARGA
async def admin_edit_deskripsi(update: Update, context: CallbackContext):
    query, kode = update.callback_query, query.data.split("|")[1]
    await query.answer()
    context.user_data["admin_edit_kode"] = kode
    admin_data = db.get_produk_admin(kode)
    deskripsi_sekarang = (admin_data and admin_data["deskripsi"]) or ""
    await query.edit_message_text(f"📝 <b>EDIT DESKRIPSI</b>\nKode: <b>{kode}</b>\nDeskripsi saat ini:\n<code>{deskripsi_sekarang}</code>\n\nKetik deskripsi baru:", parse_mode=ParseMode.HTML)
    return ADMIN_EDIT_DESKRIPSI
async def admin_edit_deskripsi_step(update: Update, context: CallbackContext):
    kode, deskripsi = context.user_data.get("admin_edit_kode"), update.message.text.strip()
    db.set_produk_admin_deskripsi(kode, deskripsi)
    await update.message.reply_text(f"✅ Deskripsi untuk <b>{kode}</b> berhasil diupdate.", parse_mode=ParseMode.HTML, reply_markup=ui.get_menu(update.effective_user.id))
    return ConversationHandler.END
async def admin_cekuser_menu(update: Update, context: CallbackContext):
    query, users = update.callback_query, db.get_all_users()
    await query.answer()
    keyboard = [[InlineKeyboardButton(f"{u[2]} (@{u[1]})", callback_data=f"admin_cekuser_detail|{u[0]}")] for u in users]
    keyboard.append(ui.btn_kembali())
    await query.edit_message_text("👥 <b>DAFTAR USER</b>\nPilih user:", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(keyboard))
    return ConversationHandler.END
async def admin_cekuser_detail_callback(update: Update, context: CallbackContext):
    query, user_id = update.callback_query, int(query.data.split("|")[1])
    await query.answer()
    user = db.get_user(user_id)
    if user:
        msg = f"👤 <b>DETAIL USER</b>\n\n<b>Nama:</b> {user[2]}\n<b>Username:</b> @{user[1]}\n<b>ID:</b> <code>{user[0]}</code>\n<b>Saldo:</b> Rp {db.get_saldo(user_id):,}\n<b>Transaksi:</b> {db.get_riwayat_jml(user_id)}"
        await query.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([ui.btn_kembali()]))
    else: await query.edit_message_text("❌ User tidak ditemukan.", reply_markup=InlineKeyboardMarkup([ui.btn_kembali()]))
    return ConversationHandler.END
async def admin_topup_pending_menu(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    items = db.get_topup_pending_all()
    keyboard = [[InlineKeyboardButton(f"{r[3]} | Rp{r[4]:,}", callback_data=f"admin_topup_detail|{r[0]}")] for r in items]
    if not keyboard: keyboard.append([InlineKeyboardButton("✅ Tidak ada top up pending", callback_data="main_menu_inline")])
    keyboard.append(ui.btn_kembali())
    await query.edit_message_text("📋 <b>PERMINTAAN TOP UP PENDING</b>", reply_markup=InlineKeyboardMarkup(keyboard))
    return ConversationHandler.END
async def admin_topup_detail(update: Update, context: CallbackContext):
    query, topup_id = update.callback_query, query.data.split("|")[1]
    await query.answer()
    r = db.get_topup_by_id(topup_id)
    if not r:
        await query.answer("❌ Data tidak ditemukan.", show_alert=True)
        return ConversationHandler.END
    caption = f"📋 <b>DETAIL TOP UP</b>\n\n👤 <b>User:</b> {r[3]} (@{r[2]})\n🆔 <b>User ID:</b> <code>{r[1]}</code>\n💰 <b>Nominal:</b> Rp {r[4]:,}\n⏰ <b>Waktu:</b> {r[5]}"
    actions = [[InlineKeyboardButton("✅ Approve", callback_data=f"admin_topup_action|approve|{topup_id}"), InlineKeyboardButton("❌ Reject", callback_data=f"admin_topup_action|reject|{topup_id}")], ui.btn_kembali()]
    if r[7]: await query.edit_message_media(InputMediaPhoto(r[7], caption=caption, parse_mode=ParseMode.HTML), reply_markup=InlineKeyboardMarkup(actions))
    else: await query.edit_message_text(caption + "\n\n❌ Belum ada bukti transfer", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup(actions))
    return ConversationHandler.END
async def admin_topup_action(update: Update, context: CallbackContext):
    query, (_, action, topup_id) = update.callback_query, query.data.split("|")
    r = db.get_topup_by_id(topup_id)
    if not r:
        await query.answer("❌ Data tidak ditemukan.", show_alert=True)
        return ConversationHandler.END
    if action == "approve":
        db.tambah_saldo(r[1], r[4])
        db.update_topup_status(topup_id, "approved")
        try: await context.bot.send_message(r[1], f"✅ <b>TOP UP DISETUJUI</b>\n\nTop up Rp {r[4]:,} telah disetujui.\nSaldo Anda: Rp {db.get_saldo(r[1]):,}", parse_mode=ParseMode.HTML)
        except Exception as e: logger.error(f"Notif approve gagal: {e}")
        await query.answer("✅ Top up disetujui.", show_alert=True)
    elif action == "reject":
        db.update_topup_status(topup_id, "rejected")
        try: await context.bot.send_message(r[1], f"❌ <b>TOP UP DITOLAK</b>\n\nTop up Rp {r[4]:,} ditolak admin.", parse_mode=ParseMode.HTML)
        except Exception as e: logger.error(f"Notif reject gagal: {e}")
        await query.answer("❌ Top up ditolak.", show_alert=True)
    return await admin_topup_pending_menu(update, context)
async def broadcast_menu(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("📢 Ketik pesan yang ingin di-broadcast:", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([ui.btn_kembali()]))
    return BC_MESSAGE
async def broadcast_step(update: Update, context: CallbackContext):
    text, users, count, fail = update.message.text, db.get_all_users(), 0, 0
    for u in users:
        try:
            await context.bot.send_message(chat_id=int(u[0]), text=f"📢 <b>BROADCAST</b>\n\n{text}", parse_mode=ParseMode.HTML)
            count += 1
        except Exception: fail += 1
    await update.message.reply_text(f"✅ <b>BROADCAST SELESAI</b>\nBerhasil: {count}, Gagal: {fail}", reply_markup=ui.get_menu(update.effective_user.id))
    return ConversationHandler.END
async def admin_generate_kode(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("🔑 <b>GENERATE KODE UNIK</b>\n\nMasukkan nominal (min 10.000):", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([ui.btn_kembali()]))
    return INPUT_KODE_UNIK
async def admin_generate_kode_step(update: Update, context: CallbackContext):
    try:
        nominal = int(update.message.text.replace(".", "").replace(",", ""))
        if nominal < 10000: raise ValueError
        kode = db.generate_kode_unik()
        db.simpan_kode_unik(kode, update.effective_user.id, nominal)
        await update.message.reply_text(f"✅ <b>KODE UNIK DIBUAT</b>\n\nKode: <code>{kode}</code>\nNominal: <b>Rp {nominal:,}</b>\n\nBerikan kode ini ke user.", parse_mode=ParseMode.HTML, reply_markup=ui.get_menu(update.effective_user.id))
    except ValueError:
        await update.message.reply_text("❌ Masukkan angka valid min 10.000")
        return INPUT_KODE_UNIK
    return ConversationHandler.END
async def lihat_saldo(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    saldo = db.get_saldo(query.from_user.id)
    await query.edit_message_text(f"💰 <b>SALDO ANDA</b>\n\nSaldo: <b>Rp {saldo:,}</b>", parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([ui.btn_kembali()]))
    return ConversationHandler.END
