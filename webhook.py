# webhook.py
import re, asyncio
from flask import Flask, request, jsonify
from config import logger, WEBHOOK_PORT
import database as db
from telegram.constants import ParseMode
from ui import get_menu
app = Flask(__name__)
RX = re.compile(r'RC=(?P<reffid>[a-f0-9-]+)\s+TrxID=(?P<trxid>\d+)\s+(?P<produk>[A-Z0-9]+)\.(?P<tujuan>\d+)\s+(?P<status_text>[A-Za-z]+)\s*(?P<keterangan>.+?)(?:\s+Saldo[\s\S]*?)?(?:\bresult=(?P<status_code>\d+))?\s*>?$', re.I)
def run_flask_app(application):
    @app.route('/webhook', methods=['GET', 'POST'])
    def webhook_handler():
        try:
            message = request.args.get('message') or request.form.get('message')
            if not message:
                logger.warning("[WEBHOOK] Pesan kosong diterima.")
                return jsonify({'ok': False, 'error': 'message kosong'}), 400
            match = RX.match(message)
            if not match:
                logger.warning(f"[WEBHOOK] Format tidak dikenali -> {message}")
                return jsonify({'ok': False, 'error': 'format tidak dikenali'}), 200
            groups = match.groupdict()
            reffid, status_text, keterangan = groups.get('reffid'), groups.get('status_text', '').lower(), groups.get('keterangan', '').strip()
            riwayat = db.get_riwayat_by_refid(reffid)
            if not riwayat:
                logger.warning(f"RefID {reffid} tidak ditemukan di database.")
                return jsonify({'ok': False, 'error': 'transaksi tidak ditemukan'}), 200
            user_id, produk_kode, _, _, harga, _, current_status, _ = riwayat
            if "sukses" in current_status.lower() or "gagal" in current_status.lower():
                logger.info(f"RefID {reffid} sudah memiliki status final. Webhook diabaikan.")
                return jsonify({'ok': True, 'message': 'Status sudah final'}), 200
            if "sukses" in status_text:
                db.kurang_saldo(user_id, harga)
                db.update_riwayat_status(reffid, "SUKSES", keterangan)
                msg = f"✅ <b>TRANSAKSI SUKSES</b>\n\nPesanan [{produk_kode}] Anda telah berhasil.\nKeterangan: {keterangan}\n\nSaldo Anda sekarang: Rp {db.get_saldo(user_id):,}"
            elif "gagal" in status_text or "batal" in status_text:
                db.update_riwayat_status(reffid, "GAGAL", keterangan)
                msg = f"❌ <b>TRANSAKSI GAGAL</b>\n\nPesanan [{produk_kode}] Anda GAGAL.\nKeterangan: {keterangan}\n\nSaldo Anda tidak dipotong."
            else:
                logger.info(f"Status webhook tidak dikenal: {status_text} untuk RefID {reffid}")
                return jsonify({'ok': True, 'message': 'Status tidak diproses'}), 200
            try:
                asyncio.run(application.bot.send_message(user_id, msg, parse_mode=ParseMode.HTML, reply_markup=get_menu(user_id)))
            except Exception as e:
                logger.error(f"Gagal kirim notif webhook ke user {user_id}: {e}")
            return jsonify({'ok': True, 'message': 'Webhook diterima'}), 200
        except Exception as e:
            logger.error(f"[WEBHOOK][ERROR] {e}", exc_info=True)
            return jsonify({'ok': False, 'error': 'internal_error'}), 500
    app.run(host='0.0.0.0', port=WEBHOOK_PORT)
