# main.py
import threading
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler
from config import TOKEN, logger
import database as db
from cache import update_produk_cache_background
from webhook import run_flask_app
from constants import *
from handlers.common import start, menu_command, handle_product_button, handle_topup_button, handle_unhandled_buttons, main_menu_callback, bantuan_menu, handle_text
from handlers.product import pilih_produk_callback, cek_stok_menu, input_tujuan_step, konfirmasi_step
from handlers.topup import topup_qris_amount, topup_kode_unik_menu, topup_upload_router, my_kode_unik_menu, topup_riwayat_menu, topup_amount_step, topup_upload_step, input_kode_unik_step
from handlers.admin import admin_panel, broadcast_menu, lihat_saldo, admin_cekuser_menu, admin_cekuser_detail_callback, admin_topup_pending_menu, admin_topup_detail, admin_topup_action, admin_produk_menu, admin_produk_detail, admin_edit_harga, admin_edit_deskripsi, admin_generate_kode, broadcast_step, admin_edit_harga_step, admin_edit_deskripsi_step, admin_generate_kode_step
from handlers.history import riwayat_user, semua_riwayat_admin
async def callback_router(update: Update, context: CallbackContext):
    query, data = update.callback_query, query.data
    logger.info(f"Callback received: {data}")
    route_map = {'main_menu_inline': main_menu_callback, 'bantuan': bantuan_menu, 'riwayat': riwayat_user, 'semua_riwayat': semua_riwayat_admin, 'cek_stok': cek_stok_menu, 'topup_riwayat': topup_riwayat_menu, 'my_kode_unik': my_kode_unik_menu, 'admin_panel': admin_panel, 'admin_cekuser': admin_cekuser_menu, 'lihat_saldo': lihat_saldo, 'admin_topup_pending': admin_topup_pending_menu, 'beli_produk': handle_product_button, 'topup_menu': handle_topup_button, 'topup_qris': topup_qris_amount, 'topup_kode_unik': topup_kode_unik_menu, 'broadcast': broadcast_menu, 'admin_produk': admin_produk_menu, 'admin_generate_kode': admin_generate_kode }
    if data.startswith("topup_upload|"): return await topup_upload_router(update, context)
    if data.startswith("admin_cekuser_detail|"): return await admin_cekuser_detail_callback(update, context)
    if data.startswith("admin_topup_detail|"): return await admin_topup_detail(update, context)
    if data.startswith("admin_topup_action|"): return await admin_topup_action(update, context)
    if data in route_map: return await route_map[data](update, context)
    return ConversationHandler.END
def main():
    db.init_db()
    logger.info("Memuat cache produk awal...")
    update_produk_cache_background()
    application = Application.builder().token(TOKEN).build()
    flask_thread = threading.Thread(target=run_flask_app, args=(application,))
    flask_thread.daemon = True
    flask_thread.start()
    logger.info("Flask webhook server starting on a separate thread.")
    
    product_button_regex = r'^(' + '|'.join([name for sublist in ui.product_layout_names for name in sublist]) + r') \(stok: \d+\)$'

    application.add_handler(MessageHandler(filters.TEXT & filters.Regex(product_button_regex), handle_product_button))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'^Topup Saldo$'), handle_topup_button))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'^(Cek Saldo|Cek Area|Unreg Mandiri|All Bekasan|Cek Dompul|Cek Stock Fresh|Cek Stock Bekasan)$'), handle_unhandled_buttons))
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start), CommandHandler('menu', menu_command), CallbackQueryHandler(callback_router)],
        states={
            CHOOSING_PRODUK: [CallbackQueryHandler(pilih_produk_callback, pattern="^produk\\|")],
            INPUT_TUJUAN: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_tujuan_step)],
            KONFIRMASI: [MessageHandler(filters.TEXT & ~filters.COMMAND, konfirmasi_step)],
            TOPUP_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, topup_amount_step)],
            TOPUP_UPLOAD: [MessageHandler(filters.PHOTO, topup_upload_step)],
            INPUT_KODE_UNIK: [MessageHandler(filters.TEXT & ~filters.COMMAND, input_kode_unik_step)],
            BC_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_step)],
            ADMIN_CEKUSER: [CallbackQueryHandler(admin_produk_detail, pattern="^admin_produk_detail\\|"), CallbackQueryHandler(admin_edit_harga, pattern="^admin_edit_harga\\|"), CallbackQueryHandler(admin_edit_deskripsi, pattern="^admin_edit_deskripsi\\|")],
            ADMIN_EDIT_HARGA: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_edit_harga_step)],
            ADMIN_EDIT_DESKRIPSI: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_edit_deskripsi_step)],
        },
        fallbacks=[CommandHandler('start', start), CommandHandler('menu', menu_command), CallbackQueryHandler(main_menu_callback, pattern="^main_menu_inline$")],
        allow_reentry=True
    )
    application.add_handler(conv_handler)
    application.add_handler(CallbackQueryHandler(callback_router))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    logger.info("Bot started...")
    application.run_polling()

if __name__ == "__main__":
    main()
