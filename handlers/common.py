# handlers/common.py
from telegram import Update, InlineKeyboardMarkup
from telegram.ext import CallbackContext, ConversationHandler
from telegram.constants import ParseMode
import database as db
import ui
from handlers.product import beli_produk_menu
from handlers.topup import topup_menu
async def start(update: Update, context: CallbackContext):
    user = update.effective_user
    db.tambah_user(user.id, user.username or "", user.full_name)
    keyboard = await ui.generate_main_keyboard()
    await update.message.reply_text(ui.dashboard_msg(user), parse_mode=ParseMode.HTML, reply_markup=keyboard)
async def menu_command(update: Update, context: CallbackContext): await start(update, context)
async def handle_product_button(update: Update, context: CallbackContext):
    class FakeQuery:
        def __init__(self, msg): self.message = msg
        async def answer(self): pass
        async def edit_message_text(self, *args, **kwargs): return await self.message.reply_text(*args, **kwargs)
    class FakeUpdate:
        def __init__(self, original_update): self.effective_user, self.callback_query = original_update.effective_user, FakeQuery(original_update.message)
    return await beli_produk_menu(FakeUpdate(update), context)
async def handle_topup_button(update: Update, context: CallbackContext):
    class FakeQuery:
        def __init__(self, msg): self.message = msg
        async def answer(self): pass
        async def edit_message_text(self, *args, **kwargs): return await self.message.reply_text(*args, **kwargs)
    class FakeUpdate:
        def __init__(self, original_update): self.effective_user, self.callback_query = original_update.effective_user, FakeQuery(original_update.message)
    return await topup_menu(FakeUpdate(update), context)
async def handle_unhandled_buttons(update: Update, context: CallbackContext): await update.message.reply_text(f"Tombol '{update.message.text}' belum memiliki fungsi.")
async def main_menu_callback(update: Update, context: CallbackContext):
    user = update.effective_user
    query = update.callback_query
    await query.answer()
    await query.message.reply_text(ui.dashboard_msg(user), parse_mode=ParseMode.HTML)
    return ConversationHandler.END
async def bantuan_menu(update: Update, context: CallbackContext):
    query = update.callback_query
    await query.answer()
    msg = "❓ <b>BANTUAN</b>\n\n[...Isi Bantuan Anda...]"
    await query.edit_message_text(msg, parse_mode=ParseMode.HTML, reply_markup=InlineKeyboardMarkup([ui.btn_kembali()]))
    return ConversationHandler.END
async def handle_text(update: Update, context: CallbackContext): await update.message.reply_text("Silakan pilih menu dari keyboard di bawah.")
