# שימוש בתמונת בסיס קלה עם Python 3.11
FROM python:3.11-slim

# הגדרת משתני סביבה
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    TELEGRAM_TOKEN="" \
    BASE_URL="https://groky.onrender.com" \
    PORT=8443

# יצירת משתמש לא-פריווילגי
RUN useradd -m -u 1000 appuser

# הגדרת ספריית עבודה
WORKDIR /app

# התקנת תלויות מערכת עבור Pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libc-dev \
    libjpeg-dev \
    zlib1g-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# העתקת קובץ התלויות
COPY requirements.txt .

# התקנת תלויות Python
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# העתקת שאר הקבצים
COPY . .

# וידוא שקובץ thumbnail.jpg ו-words_to_remove.txt קיימים
RUN test -f thumbnail.jpg || { echo "thumbnail.jpg not found!"; exit 1; } && \
    test -f words_to_remove.txt || { echo "words_to_remove.txt not found!"; exit 1; }

# שינוי הרשאות למשתמש appuser
RUN chown -R appuser:appuser /app

# מעבר למשתמש לא-פריווילגי
USER appuser

# פקודה להרצת הבוט
CMD ["python", "bot.py"]