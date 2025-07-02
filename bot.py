import os
import logging
import io
import re
import asyncio
from PIL import Image
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ContextTypes, filters
)

# הגדרות
THUMBNAIL_PATH = 'thumbnail.jpg'
WORDS_FILE_PATH = 'words_to_remove.txt'
BASE_URL = os.getenv('BASE_URL', 'https://groky.onrender.com')
PORT = int(os.getenv('PORT', 8443))
TOKEN = os.getenv('TELEGRAM_TOKEN')

# לוג בסיסי
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ניקוי שם קובץ
def remove_english_words(filename: str) -> str:
    try:
        base, ext = os.path.splitext(filename)
        if not os.path.exists(WORDS_FILE_PATH):
            return filename
        with open(WORDS_FILE_PATH, encoding='utf-8') as f:
            for word in f:
                base = re.sub(re.escape(word.strip()), '', base, flags=re.IGNORECASE)
        base = re.sub(r'[_\s]+', ' ', base.strip()) or 'file'
        return f"{base}{ext}"
    except Exception as e:
        logger.warning(f"שגיאה בניקוי שם קובץ: {e}")
        return filename

# יצירת thumbnail
def create_thumbnail() -> io.BytesIO | None:
    try:
        with Image.open(THUMBNAIL_PATH) as img:
            img.thumbnail((200, 300))
            thumb_io = io.BytesIO()
            img.save(thumb_io, format='JPEG', quality=85)
            thumb_io.seek(0)
            return thumb_io
    except Exception as e:
        logger.warning(f"שגיאה ביצירת thumbnail: {e}")
        return None

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        'היי! אני גרוקי.\nשלח לי קובץ, ואחזיר אותו עם תמונה ושם מתוקן.\n/help לעזרה.'
    )

# /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        'שלח לי קובץ:\n- אמחק מילים מסוימות מהשם\n- אוסיף לו תמונה\n- ואחזיר אותו בשם חדש\n'
        'זהו. פשוט ואלגנטי.'
    )

# קבלת קובץ
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    doc = update.message.document
    await update.message.reply_text('טוען...')
    try:
        file_path = f"temp_{doc.file_name}"
        await doc.get_file().download_to_drive(file_path)

        thumb_io = create_thumbnail()
        cleaned_name = remove_english_words(doc.file_name)
        base, ext = os.path.splitext(cleaned_name)
        new_name = f"{base.strip().replace(' ', '_')}_OldTown{ext}"

        with open(file_path, 'rb') as f:
            await context.bot.send_document(
                chat_id=update.message.chat_id,
                document=f,
                filename=new_name,
                thumbnail=thumb_io,
                caption='ספריית אולדטאון - https://t.me/OldTownew'
            )

        os.remove(file_path)
    except Exception as e:
        logger.error(f"שגיאה בקובץ: {e}")
        await update.message.reply_text('שגיאה! נסה שוב.')

# שגיאות כלליות
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.warning(f"שגיאה: {context.error}")
    if isinstance(update, Update) and update.message:
        await update.message.reply_text('תקלה זמנית. נסה שוב.')

# הפעלת הבוט
async def main():
    if not TOKEN or not BASE_URL.startswith('https://'):
        logger.error("חסרים ערכים קריטיים (TOKEN/BASE_URL)"); return
    if not os.path.exists(THUMBNAIL_PATH):
        logger.error(f"{THUMBNAIL_PATH} לא נמצא"); return

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('help', help_command))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))
    app.add_error_handler(error_handler)

    webhook_url = f"{BASE_URL}/{TOKEN}"
    await app.initialize()
    await app.bot.set_webhook(url=webhook_url)
    await app.start()
    await app.updater.start_webhook(
        listen='0.0.0.0', port=PORT, url_path=TOKEN, webhook_url=webhook_url
    )

    logger.info(f"Webhook פעיל על {webhook_url}")
    try:
        while True:
            await asyncio.sleep(3600)
    except:
        pass
    finally:
        await app.stop()
        await app.shutdown()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("עצירה ידנית")