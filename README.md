# Bot Kuota Akrab XL Axis

![Telegram Bot](https://img.shields.io/badge/Telegram-Bot-blue?style=for-the-badge&logo=telegram)
![Python](https://img.shields.io/badge/Python-3.8+-yellow?style=for-the-badge&logo=python)
![Flask](https://img.shields.io/badge/Flask-Webhooks-grey?style=for-the-badge&logo=flask)

Bot Telegram ini dirancang untuk mengelola penjualan produk kuota Akrab XL/Axis. Bot ini memiliki struktur modular, panel admin, dan fitur menu keyboard dinamis yang menampilkan stok produk secara real-time.

Repositori ini dapat diakses di: https://github.com/amifistore/Fikri](https://github.com/amifistore/Fikri)

---
## ✨ Fitur Utama

- **Struktur Modular**: Kode dipecah menjadi beberapa file berdasarkan fungsi (`handlers`, `database`, `ui`, dll.) agar mudah dikelola dan dikembangkan.
- **Asynchronous**: Dibangun menggunakan `python-telegram-bot` versi 20+ dengan `async/await` untuk performa tinggi.
- **Menu Dinamis**: Menu utama berupa `ReplyKeyboard` yang menampilkan stok produk terkini langsung dari API.
- **Alur Transaksi Aman**: Saldo pengguna hanya dipotong setelah transaksi dikonfirmasi berhasil oleh provider melalui webhook.
- **Panel Admin**: Fitur lengkap untuk admin, termasuk manajemen produk, broadcast ke semua pengguna, dan persetujuan top up manual.
- **Top Up Otomatis**: Mendukung top up via QRIS dinamis dan kode unik manual.

---
## 📋 Prasyarat

Sebelum memulai, pastikan Anda memiliki:
- Server/VPS dengan OS Linux (disarankan Debian/Ubuntu).
- **Python 3.8** atau versi lebih baru.
- **pip** (manajer paket Python).
- **Git** untuk mengkloning repositori.

---
## 🚀 Langkah Instalasi

Ikuti langkah-langkah berikut dengan teliti di terminal server Anda.

### 1. Kloning Repositori
Pindahkan repositori ini ke server Anda menggunakan Git.
```bash
git clone [https://github.com/amifistore/Fikri.git](https://github.com/amifistore/Fikri.git)
cd Fikri
# Buat dan aktifkan venv
python3 -m venv venv
source venv/bin/activate

# Buat file requirements.txt
nano requirements.txt

# Instal semua dependensi
pip install -r requirements.txt
