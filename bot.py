# טיפול בקבצים
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    document = update.message.document
    await update.message.reply_text('קיבלתי את הקובץ, רגע אחד...')

    try:
        # הורדת הקובץ — תיקון כאן!
        file_obj = await document.get_file()  # הוספנו await כאן
        input_file = f'temp_{document.file_name}'
        await file_obj.download_to_drive(input_file)

        # הכנת thumbnail
        thumb_io = await prepare_thumbnail()
        error_message = None
        if not thumb_io:
            error_message = 'לא הצלחתי להוסיף תמונה, אבל הנה הקובץ שלך.'

        # הסרת מילים מוגדרות משם הקובץ
        original_filename = document.file_name
        cleaned_filename = remove_english_words(original_filename)
        
        # הוספת "_OldTown" לפני הסיומת, תוך המרת רווחים ל-_ בסוף השם
        base, ext = os.path.splitext(cleaned_filename)
        base = base.strip()
        new_filename = f"{base.replace(' ', '_')}_OldTown{ext}"

        # שליחת הקובץ
        with open(input_file, 'rb') as f:
            await context.bot.send_document(
                chat_id=update.message.chat_id,
                document=f,
                filename=new_filename,
                thumbnail=thumb_io if thumb_io else None,
                caption=error_message or 'ספריית אולדטאון - https://t.me/OldTownew'
            )

        # ניקוי קבצים זמניים
        os.remove(input_file)

    except Exception as e:
        logger.error(f"שגיאה בטיפול בקובץ: {e}")
        await update.message.reply_text('משהו השתבש. תנסה שוב?')