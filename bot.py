import os
from threading import Thread
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from flask import Flask

TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("Falta BOT_TOKEN")

# --- Telegram bot ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot activo, escribiste /start")

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("pong")

def run_telegram():
    tg_app = Application.builder().token(TOKEN).build()
    tg_app.add_handler(CommandHandler("start", start))
    tg_app.add_handler(CommandHandler("ping", ping))
    print("Bot corriendo en Render (polling)…")
    tg_app.run_polling()

# --- Mini servidor web (para Render) ---
flask_app = Flask(__name__)

@flask_app.get("/")
def home():
    return "OK", 200

def run_web():
    port = int(os.environ.get("PORT", "10000"))
    print(f"HTTP vivo en puerto {port}")
    flask_app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    Thread(target=run_telegram, daemon=True).start()
    run_web()
