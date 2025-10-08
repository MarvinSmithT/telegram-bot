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
OWNER_ID = int(os.environ.get("OWNER_ID", "0"))

def is_owner(update: Update) -> bool:
    return update.effective_user and update.effective_user.id == OWNER_ID
app = None  # se asigna más abajo cuando se crea la app de Telegram
PUBLIC_URL = os.environ.get("PUBLIC_URL", "")
TG_SECRET = os.environ.get("TG_SECRET", "")

# --- Comandos del bot ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Bot activo, escribiste /start")

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("pong")

async def post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        await update.message.reply_text("⛔ No autorizado.")
        return

    if not context.args:
        await update.message.reply_text("Uso: /post tu mensaje")
        return
    msg = " ".join(context.args)
    await context.bot.send_message(chat_id=CHANNEL_ID, text=msg)
    await update.message.reply_text("✅ Enviado al canal.")
async def postphoto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update):
        await update.message.reply_text("⛔ No autorizado.")
        return

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
from datetime import datetime  # si no está ya importado, añádelo arriba del archivo

async def signal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Uso:
    /signal PAR|DIRECCION|ENTRADA|SL|TP|TF
    Ejemplo:
    /signal EURUSD|BUY|1.08420|1.08320|1.08620|M5
    """
    if not is_owner(update):
        await update.message.reply_text("⛔ No autorizado.")
        return

    text = " ".join(context.args)
    parts = [p.strip() for p in text.split("|")]
    if len(parts) < 6:
        await update.message.reply_text(
            "Uso: /signal PAR|DIRECCION|ENTRADA|SL|TP|TF\n"
            "Ej: /signal EURUSD|BUY|1.08420|1.08320|1.08620|M5"
        )
        return

    par, side, entry, sl, tp, tf = parts[:6]
    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    body = (
        "📈 <b>SEÑAL</b>\n"
        f"• <b>Par:</b> {par}\n"
        f"• <b>Dirección:</b> {side.upper()}\n"
        f"• <b>Entrada:</b> {entry}\n"
        f"• <b>SL:</b> {sl}\n"
        f"• <b>TP:</b> {tp}\n"
        f"• <b>TF:</b> {tf}\n"
        f"• <b>Hora:</b> {now}"
    )

    await context.bot.send_message(chat_id=CHANNEL_ID, text=body, parse_mode="HTML")
    await update.message.reply_text("✅ Señal enviada al canal.")

# --- Mini servidor web para Render ---
flask_app = Flask(__name__)

@flask_app.get("/")
def home():
    return "OK", 200
# --- Telegram Webhook ---
@flask_app.post(f"/tg/{os.environ.get('TG_SECRET','')}")
def tg_webhook():
    from flask import request
    import asyncio
    from telegram import Update

    if not TG_SECRET:
        return ("no TG_SECRET", 500)
    if app is None:
        return ("app not ready", 503)

    data = request.get_json(silent=True) or {}
    try:
        upd = Update.de_json(data, app.bot)
app.create_task(app.process_update(upd))
return ("ok", 200)

    except Exception as e:
        return (f"err: {e}", 500)
    
# --- TradingView Webhook ---
@flask_app.post("/tv")
def tv_webhook():
    # imports locales para no mover los de arriba
    from flask import request
    import asyncio, json

    tv_secret = os.environ.get("TV_SECRET", "")
    # 1) Validar secreto
    secret = request.args.get("secret")
    if not secret:
        data0 = request.get_json(silent=True) or {}
        secret = data0.get("secret") or request.headers.get("X-TRADINGVIEW-SECRET")
    if tv_secret and secret != tv_secret:
        return ("unauthorized", 401)

    # 2) Leer mensaje y enviarlo al canal
    data = request.get_json(silent=True) or {}
    text = data.get("text") or data.get("message") or json.dumps(data, ensure_ascii=False)
    if app is None:
        return ("app not ready", 503)

app.create_task(app.bot.send_message(chat_id=CHANNEL_ID, text=f"📢 TradingView: {text}"))
return ("ok", 200)

# GET de prueba rápida desde el navegador (opcional)
@flask_app.get("/tv")
def tv_test():
    from flask import request
    import asyncio
    tv_secret = os.environ.get("TV_SECRET", "")
    if tv_secret and request.args.get("secret") != tv_secret:
        return ("unauthorized", 401)
    text = request.args.get("text", "test")
    if app is None:
        return ("app not ready", 503)
    
app.create_task(app.bot.send_message(chat_id=CHANNEL_ID, text=f"🔧 TV TEST: {text}"))
return ("ok", 200)

def run_web():
    port = int(os.environ.get("PORT", "10000"))
    print(f"HTTP vivo en puerto {port}")
    flask_app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    import asyncio

    # 1) Crear la app de Telegram
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ping", ping))
    app.add_handler(CommandHandler("post", post))
    app.add_handler(CommandHandler("postphoto", postphoto))
    app.add_handler(CommandHandler("signal", signal))

    # 2) Levantar Flask (HTTP) en segundo plano
    Thread(target=run_web, daemon=True).start()
    print("HTTP vivo (Flask) + inicializando Telegram…")

    async def _start_webhook():
        # Inicializar y arrancar PTB sin polling
        await app.initialize()
        await app.start()

        # Asegurar que NO haya polling activo ni webhooks viejos
        try:
            await app.bot.delete_webhook(drop_pending_updates=True)
        except Exception:
            pass

        # Registrar webhook de Telegram hacia tu Flask
        if PUBLIC_URL and TG_SECRET:
            url = f"{PUBLIC_URL}/tg/{TG_SECRET}"
            await app.bot.set_webhook(url=url)
            print(f"Webhook de Telegram activo → {url}")
        else:
            print("Faltan PUBLIC_URL o TG_SECRET en Environment.")

        # Mantener viva la tarea
        await asyncio.Event().wait()

    # 3) Correr la tarea async en el hilo principal
    asyncio.run(_start_webhook())

