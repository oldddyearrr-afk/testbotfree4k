# استخدام نسخة Alpine فائقة الخفة
FROM python:3.11-alpine

# تثبيت FFmpeg المصغر وتنظيف المخلفات فوراً
RUN apk add --no-cache ffmpeg

WORKDIR /app

# تثبيت المكتبات
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نسخ الكود
COPY . .

# تشغيل البوت
CMD ["python", "main.py"]
