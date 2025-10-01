import os
from threading import Thread
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    raise RuntimeError("Falta BOT_TOKEN")

# --- Handlers del bot ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot activo, escribiste /start")

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("pong")

# --- Mini servidor web para Render ---
flask_app = Flask(__name__)

@flask_app.get("/")
def home():
    return "OK", 200

def run_web():
    port = int(os.environ.get("PORT", "10000"))
    print(f"HTTP vivo en puerto {port}")
    flask_app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    # Levanta Flask en segundo plano
    Thread(target=run_web, daemon=True).start()

    # Bot en el hilo principal (asyncio ok)
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ping", ping))
    print("Bot corriendo en Render (polling)…")
    app.run_polling()

