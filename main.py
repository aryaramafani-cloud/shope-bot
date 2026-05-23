import os, json, logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from shopee_bot import ShopeeBot
from config import TELEGRAM_BOT_TOKEN, COOKIE_TEMP_PATH

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

VERSION = "2.1"
cookie_ready = False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"🤖 **Shopee Auto Checkout v{VERSION}**\n\n"
        "📌 Cara pakai:\n"
        "1. Kirim file .json (lampiran → File) yang berisi cookie.\n"
        "2. /buy <link_produk>\n"
        "3. Bot checkout + voucher otomatis.\n\n"
        "Contoh: /buy https://shopee.co.id/produk-i.123.456\n\n"
        "⚠️ Karena JSON cookie biasanya panjang, jangan paste teks. Kirim saja sebagai file."
    )

async def receive_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global cookie_ready
    doc = update.message.document
    if not doc:
        if update.message.effective_attachment:
            doc = update.message.effective_attachment
        else:
            return

    if doc.file_name.endswith('.json'):
        try:
            file = await doc.get_file()
            await file.download_to_drive(COOKIE_TEMP_PATH)
            with open(COOKIE_TEMP_PATH, 'r') as f:
                data = json.load(f)

            # Tangani jika data adalah dict (objek), bukan list
            if isinstance(data, list):
                # sudah benar
                pass
            elif isinstance(data, dict):
                # bungkus ke dalam list
                data = [data]
                with open(COOKIE_TEMP_PATH, 'w') as f:
                    json.dump(data, f)
            else:
                await update.message.reply_text("❌ Format tidak dikenali. Harus array/objek JSON.")
                os.remove(COOKIE_TEMP_PATH)
                return

            cookie_ready = True
            await update.message.reply_text("✅ Cookie valid dan siap. Kirim /buy <link>")

        except json.JSONDecodeError:
            await update.message.reply_text("❌ File bukan JSON yang valid.")
            if os.path.exists(COOKIE_TEMP_PATH):
                os.remove(COOKIE_TEMP_PATH)
        except Exception as e:
            logger.error(f"Gagal proses file: {e}")
            await update.message.reply_text("❌ Gagal membaca file.")
    else:
        await update.message.reply_text("❌ Hanya file .json yang diterima.")

async def receive_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ℹ️ Silakan kirim **file .json** (bukan teks). Lihat /start.")

async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global cookie_ready
    if not cookie_ready:
        await update.message.reply_text("❌ Belum ada cookie. Kirim file .json dulu.")
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
        logger.error(f"Error checkout: {e}")
        await update.message.reply_text(f"❌ Error: {e}")
    finally:
        bot.close()
        if os.path.exists(COOKIE_TEMP_PATH):
            os.remove(COOKIE_TEMP_PATH)
        cookie_ready = False

async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global cookie_ready
    await update.message.reply_text(
        f"🟢 v{VERSION} | Cookie: {'Siap' if cookie_ready else 'Belum ada'}"
    )

def main():
    if TELEGRAM_BOT_TOKEN == "ISI_TOKEN_BOT_KAMU_DISINI":
        print("⚠️  Token belum diisi di config.py!")
        return
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("buy", buy))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(MessageHandler(filters.Document.ALL, receive_file))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_text))
    logger.info(f"Bot v{VERSION} berjalan...")
    app.run_polling()

if __name__ == '__main__':
    main()
