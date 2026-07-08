import os
import sys
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from dotenv import load_dotenv

load_dotenv()

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from telegram_bot.handlers import (
  handle_message,
  handle_photo,
  handle_start,
  handle_recent,
  handle_structure,
)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not TELEGRAM_BOT_TOKEN:
  raise ValueError("TELEGRAM_BOT_TOKEN is not set. Check your .env file.")
  
def main() -> None:
  """Build the bot application, register handlers, start polling."""
  app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
  
  app.add_handler(CommandHandler("start", handle_start))
  app.add_handler(CommandHandler("recent", handle_recent))
  app.add_handler(CommandHandler("structure", handle_structure))
  app.add_handler(MessageHandler(filters.PHOTO | filters.Document.IMAGE, handle_photo))
  app.add_handler(MessageHandler(filters.TEXT, ~filters.COMMAND, handle_message))
  
  WEBHOOK_URL = os.getenv("WEBHOOK_URL")
  PORT = int(os.environ.get("PORT", 8443))
  print(f"Xoxobot starting webhook on port {PORT}")
  app.run_webhook(
    listen="0.0.0.0",
    port=PORT,
    webhook_url=WEBHOOK_URL,
  )
  
if __name__ == "__main__":
  main()