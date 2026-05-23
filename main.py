import os, json
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from shopee_bot import ShopeeBot
from config import TELEGRAM_BOT_TOKEN, COOKIE_TEMP_PATH

cookie_ready = False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 **Shopee Auto Checkout**\n\n"
        "1. Copy cookie pakai ekstensi 'Copy Cookies' (pilih **Copy as JSON**).\n"
        "2. Paste teks JSON-nya ke sini.\n"
        "3. /buy <link_produk>\n"
        "4. Bot checkout + voucher otomatis.\n\n"
        "Contoh: /buy https://shopee.co.id/produk-i.123.456"
    )

async def receive_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global cookie_ready
    text = update.message.text.strip()
    try:
        data = json.loads(text)
        if isinstance(data, list):
            with open(COOKIE_TEMP_PATH, 'w') as f:
                json.dump(data, f)
            cookie_ready = True
            await update.message.reply_text("✅ Cookie siap. Kirim /buy <link>")
        else:
            await update.message.reply_text("❌ Format harus list JSON.")
    except json.JSONDecodeError:
        pass  # abaikan pesan biasa

async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global cookie_ready
    if not cookie_ready:
        await update.message.reply_text("❌ Kirim dulu teks cookie.")
        return
    if not context.args:
        await update.message.reply_text("❌ Format: /buy <link>")
        return

    url = context.args[0]
    await update.message.reply_text("⏳ Checkout...")
    bot = ShopeeBot(COOKIE_TEMP_PATH)
    try:
        bot.login_via_cookie()
        success = bot.checkout(url)
        if success:
            await update.message.reply_text("✅ **Checkout berhasil! Voucher sudah menempel.**")
        else:
            await update.message.reply_text("❌ Gagal checkout.")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")
    finally:
        bot.close()
        if os.path.exists(COOKIE_TEMP_PATH):
            os.remove(COOKIE_TEMP_PATH)
        cookie_ready = False

async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global cookie_ready
    await update.message.reply_text(
        "🟢 Siap checkout." if cookie_ready else "🟡 Belum ada cookie."
    )

def main():
    if TELEGRAM_BOT_TOKEN == "ISI_TOKEN_BOT_KAMU_DISINI":
        print("⚠️  Token belum diisi!")
        return
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("buy", buy))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_text))
    print("Bot berjalan...")
    app.run_polling()

if __name__ == '__main__':
    main()
