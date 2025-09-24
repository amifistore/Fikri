from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
import logging

# Setup logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

def start(update: Update, context: CallbackContext):
    update.message.reply_text('Bot started!')

def main():
    # Ganti dengan token bot Anda
    updater = Updater("YOUR_BOT_TOKEN", use_context=True)
    
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
