# config.py
import json, logging
try:
    with open("config.json") as f: cfg = json.load(f)
except Exception as e: print(f"Error membaca config.json: {e}"); exit()
TOKEN = cfg["TOKEN"]
ADMIN_IDS = [int(i) for i in cfg["ADMIN_IDS"]]
BASE_URL = cfg["BASE_URL"]
API_KEY = cfg["API_KEY"]
BASE_URL_AKRAB = cfg.get("BASE_URL_AKRAB", "")
QRIS_STATIS = cfg.get("QRIS_STATIS", "")
WEBHOOK_PORT = cfg.get("WEBHOOK_PORT", 5000)
logging.basicConfig(filename='bot_error.log', level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
CACHE_DURATION = 300
DBNAME = "botdata.db"
