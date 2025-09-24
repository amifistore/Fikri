# handlers/history.py
from telegram import Update, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import CallbackContext, ConversationHandler
import database as db
import ui
async def riwayat_user(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    items = db.get_riwayat_user(query.from_user.id)
    msg = "📋 <b>RIWAYAT TRANSAKSI ANDA</b>\n\n"
    if not items: msg += "Belum ada transaksi."
    else:
        for r in items: msg += f"{'✅' if 'SUKSES' in r[6].upper() else ('❌' if 'GAGAL' in r[6].upper() or 'BATAL' in r[6].upper() else '⏳')} <b>{r[5]}</b>\nID: <code>{r[0]}</code>\nProduk: [{r[2]}] ke {r[3]}\nHarga: Rp {r[4]:,}\nStatus: <b>{r[6].upper()}</b>\nKet: {r[7]}\n\n"
    await query.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([ui.btn_kembali()]))
    return ConversationHandler.END
async def semua_riwayat_admin(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    items = db.get_all_riwayat()
    msg = "📋 <b>SEMUA RIWAYAT TRANSAKSI</b>\n\n"
    if not items: msg += "Belum ada transaksi."
    else:
        for r in items:
            user = db.get_user(r[1])
            username = f"@{user[1]}" if user and user[1] else f"ID: {r[1]}"
            msg += f"{'✅' if 'SUKSES' in r[6].upper() else ('❌' if 'GAGAL' in r[6].upper() or 'BATAL' in r[6].upper() else '⏳')} <b>{r[5]}</b>\nUser: {username}\nProduk: [{r[2]}] ke {r[3]}\nHarga: Rp {r[4]:,}\nStatus: <b>{r[6].upper()}</b>\nKet: {r[7]}\n\n"
    await query.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([ui.btn_kembali()]))
    return ConversationHandler.END
