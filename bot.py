import os
import io
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

# הגדרת הלוגינג
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# רשימת מילים להסרה מהשם
REMOVE_WORDS = ["oldtown", "book", "ebook", "download", "free", "read", "library"]

# פונקציה להסרת מילים באנגלית בלבד
def remove_english_words(filename: str) -> str:
    name, ext = os.path.splitext(filename)
    words = name.split()
    cleaned_words = [w for w in words if w.lower() not in REMOVE_WORDS]
    cleaned_name = ' '.join(cleaned_words)
    return cleaned_name + ext

# יצירת thumbnail זמני
async def prepare_thumbnail() -> io.BytesIO | None:
    thumb_path = 'default_thumb.jpg'
    if not os.path.exists(thumb_path):
        return None
    with open(thumb_path, 'rb') as f:
        return io.BytesIO(f.read())

# התחלה
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("שלח לי קובץ EPUB או PDF ואחזיר לך אותו עם שם יפה ותמונה 📚")

# טיפול בקבצים
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    document = update.message.document
    await update.message.reply_text('קיבלתי את הקובץ, רגע אחד...')

    try:
        file_obj = await document.get_file()
        input_file = f'temp_{document.file_name}'
        await file_obj.download_to_drive(input_file)

        # הכנת thumbnail
        thumb_io = await prepare_thumbnail()
        error_message = None
        if not thumb_io:
            error_message = 'לא הצלחתי להוסיף תמונה, אבל הנה הקובץ שלך.'

        # הסרת מילים מהשם (בלי לשנות רווחים!)
        original_filename = document.file_name
        cleaned_filename = remove_english_words(original_filename)
        base, ext = os.path.splitext(cleaned_filename)

        # הפיכת _ לרווחים (למקרה שהיה במקור)
        base = base.replace('_', ' ').strip()
        new_filename = f"{base} OldTown{ext}"

        # שליחת הקובץ
        with open(input_file, 'rb') as f:
            await context.bot.send_document(
                chat_id=update.message.chat_id,
                document=f,
                filename=new_filename,
                thumbnail=thumb_io if thumb_io else None,
                caption=error_message or 'ספריית אולדטאון - https://t.me/OldTownew'
            )

        os.remove(input_file)

    except Exception as e:
        logger.error(f"שגיאה בטיפול בקובץ: {e}")
        await update.message.reply_text('משהו השתבש. תנסה שוב?')

# הרצת הבוט
def main():
    token = os.getenv("BOT_TOKEN")
    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))

    app.run_polling()

if __name__ == "__main__":
    main()