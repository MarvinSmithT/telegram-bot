import os
from threading import Thread
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.environ.get("BOT_TOKEN")
CHANNEL_ID = os.environ.get("CHANNEL_ID")

if not TOKEN:
    raise RuntimeError("Falta BOT_TOKEN")
if not CHANNEL_ID:
    raise RuntimeError("Falta CHANNEL_ID")
CHANNEL_ID = int(CHANNEL_ID)

# --- Comandos del bot ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot activo, escribiste /start")

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("pong")

async def post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Uso: /post tu mensaje")
        return
    msg = " ".join(context.args)
    await context.bot.send_message(chat_id=CHANNEL_ID, text=msg)
    await update.message.reply_text("✅ Enviado al canal.")
async def postphoto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Uso: /postphoto URL_de_imagen [texto opcional]")
        return
    url = context.args[0]
    caption = " ".join(context.args[1:]) if len(context.args) > 1 else None
    try:
        await context.bot.send_photo(chat_id=CHANNEL_ID, photo=url, caption=caption)
        await update.message.reply_text("✅ Foto enviada al canal.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error enviando foto: {e}")

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
    Thread(target=run_web, daemon=True).start()

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ping", ping))
    app.add_handler(CommandHandler("post", post))
    app.add_handler(CommandHandler("postphoto", postphoto))

    print("Bot corriendo en Render (polling)…")
    app.run_polling()

