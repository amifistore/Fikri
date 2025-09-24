# main.py
import re, threading
from telegram import Update
from telegram.ext import (
    Updater, CommandHandler, CallbackQueryHandler, MessageHandler, 
    Filters, ConversationHandler, CallbackContext
)
from config import TOKEN, logger
import database as db
from cache import update_produk_cache_background
from webhook import run_flask_app
from constants import *
import ui

# Import semua handler
from handlers.common import (
    start, menu_command, handle_product_button, handle_topup_button, 
    handle_unhandled_buttons, main_menu_callback, bantuan_menu, handle_text
)
from handlers.product import (
    beli_produk_menu, pilih_produk_callback, cek_stok_menu, 
    input_tujuan_step, konfirmasi_step
)
from handlers.topup import (
    topup_qris_amount, topup_kode_unik_menu, topup_upload_router, 
    my_kode_unik_menu, topup_riwayat_menu, topup_amount_step, 
    topup_upload_step, input_kode_unik_step
)
from handlers.admin import (
    admin_panel, broadcast_menu, lihat_saldo, admin_cekuser_menu, 
    admin_cekuser_detail_callback, admin_topup_pending_menu, 
    admin_topup_detail, admin_topup_action, admin_produk_menu, 
    admin_produk_detail, admin_edit_harga, admin_edit_deskripsi, 
    admin_generate_kode, broadcast_step, admin_edit_harga_step, 
    admin_edit_deskripsi_step, admin_generate_kode_step
)
from handlers.history import riwayat_user, semua_riwayat_admin


def callback_router(update, context):
    query = update.callback_query
    query.answer()
    data = query.data
    logger.info(f"Callback received: {data}")
    
    # Peta rute untuk callback dari inline keyboard
    route_map = {
        'main_menu_inline': main_menu_callback,
        'bantuan': bantuan_menu,
        'riwayat': riwayat_user,
        'semua_riwayat': semua_riwayat_admin,
        'cek_stok': cek_stok_menu,
        'topup_riwayat': topup_riwayat_menu,
        'my_kode_unik': my_kode_unik_menu,
        'admin_panel': admin_panel,
        'admin_cekuser': admin_cekuser_menu,
        'lihat_saldo': lihat_saldo,
        'admin_topup_pending': admin_topup_pending_menu,
        'beli_produk': beli_produk_menu,
        'topup_menu': handle_topup_button,
        'topup_qris': topup_qris_amount,
        'topup_kode_unik': topup_kode_unik_menu,
        'broadcast': broadcast_menu,
        'admin_produk': admin_produk_menu,
        'admin_generate_kode': admin_generate_kode,
    }

    if data.startswith("topup_upload|"): 
        return topup_upload_router(update, context)
    if data.startswith("admin_cekuser_detail|"): 
        return admin_cekuser_detail_callback(update, context)
    if data.startswith("admin_topup_detail|"): 
        return admin_topup_detail(update, context)
    if data.startswith("admin_topup_action|"): 
        return admin_topup_action(update, context)
    
    if data in route_map:
        return route_map[data](update, context)
        
    return ConversationHandler.END


def main():
    db.init_db()
    logger.info("Memuat cache produk awal...")
    update_produk_cache_background()
    
    # Gunakan Updater untuk versi 13.7
    updater = Updater(TOKEN, use_context=True)
    dispatcher = updater.dispatcher
    
    flask_thread = threading.Thread(target=run_flask_app, args=(updater,))
    flask_thread.daemon = True
    flask_thread.start()
    logger.info("Flask webhook server starting on a separate thread.")
    
    # Regex untuk tombol produk dinamis
    product_names = ['SuperMini', 'Mini', 'Big', 'Jumbo V2', 'JUMBO', 'MegaBig']
    product_button_regex = r'^(' + '|'.join(re.escape(name) for name in product_names) + r') \(stok: \d+\)$'

    # Regex untuk tombol statis lainnya
    static_button_regex = r'^(Topup Saldo|Cek Saldo|Cek Area|Unreg Mandiri|All Bekasan|Cek Dompul|Cek Stock Fresh|Cek Stock Bekasan)$'

    # Menambahkan handler untuk tombol ReplyKeyboard
    dispatcher.add_handler(MessageHandler(Filters.text & Filters.regex(product_button_regex), handle_product_button))
    dispatcher.add_handler(MessageHandler(Filters.text & Filters.regex(r'^Topup Saldo$'), handle_topup_button))
    dispatcher.add_handler(MessageHandler(Filters.text & Filters.regex(static_button_regex), handle_unhandled_buttons))
    
    # Conversation handler
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start),
            CommandHandler('menu', menu_command),
            CallbackQueryHandler(callback_router)
        ],
        states={
            CHOOSING_PRODUK: [CallbackQueryHandler(pilih_produk_callback, pattern="^produk\\|")],
            INPUT_TUJUAN: [MessageHandler(Filters.text & ~Filters.command, input_tujuan_step)],
            KONFIRMASI: [MessageHandler(Filters.text & ~Filters.command, konfirmasi_step)],
            TOPUP_AMOUNT: [MessageHandler(Filters.text & ~Filters.command, topup_amount_step)],
            TOPUP_UPLOAD: [MessageHandler(Filters.photo, topup_upload_step)],
            INPUT_KODE_UNIK: [MessageHandler(Filters.text & ~Filters.command, input_kode_unik_step)],
            BC_MESSAGE: [MessageHandler(Filters.text & ~Filters.command, broadcast_step)],
            ADMIN_CEKUSER: [
                CallbackQueryHandler(admin_produk_detail, pattern="^admin_produk_detail\\|"),
                CallbackQueryHandler(admin_edit_harga, pattern="^admin_edit_harga\\|"),
                CallbackQueryHandler(admin_edit_deskripsi, pattern="^admin_edit_deskripsi\\|")
            ],
            ADMIN_EDIT_HARGA: [MessageHandler(Filters.text & ~Filters.command, admin_edit_harga_step)],
            ADMIN_EDIT_DESKRIPSI: [MessageHandler(Filters.text & ~Filters.command, admin_edit_deskripsi_step)],
        },
        fallbacks=[
            CommandHandler('start', start),
            CommandHandler('menu', menu_command),
            CallbackQueryHandler(main_menu_callback, pattern="^main_menu_inline$")
        ],
        allow_reentry=True
    )
    
    dispatcher.add_handler(conv_handler)
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_text))
    
    logger.info("Bot started...")
    updater.start_polling()
    updater.idle()


if __name__ == "__main__":
    main()
