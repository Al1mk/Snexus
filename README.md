# Snexus Telegram Bot

ربات تلگرام چندمنظوره Snexus با قابلیت‌های دانلود موسیقی، ویدیو، مدیریت پلی‌لیست و سیستم اشتراک VIP

## قابلیت‌ها

- دانلود موسیقی از پلتفرم‌های مختلف (Spotify, Apple Music, SoundCloud, YouTube Music)
- دانلود محتوا از اینستاگرام (ویدیو، ریلز، استوری، پروفایل)
- مدیریت پلی‌لیست‌های شخصی
- سیستم اشتراک VIP با دانلود نامحدود
- پنل مدیریت برای ادمین‌ها
- مدیریت کانال‌های جوین اجباری

## پیش‌نیازها

- Python 3.10+
- MySQL
- FFmpeg (برای پردازش فایل‌های صوتی و تصویری)

## نصب و راه‌اندازی

1. کلون کردن مخزن:
```bash
git clone https://github.com/Al1mk/Snexus.git
cd Snexus
```

2. ایجاد محیط مجازی:
```bash
python3 -m venv venv
source venv/bin/activate  # در لینوکس
# یا
venv\Scripts\activate  # در ویندوز
```

3. نصب وابستگی‌ها:
```bash
pip install -r requirements.txt
```

4. ایجاد فایل `.env` بر اساس نمونه:
```bash
cp config/.env.example config/.env
# سپس فایل .env را با اطلاعات خود ویرایش کنید
```

5. راه‌اندازی دیتابیس:
```bash
python database/setup_db.py
```

6. اجرای ربات:
```bash
python bot.py
```

## استفاده با داکر

1. ساخت ایمیج:
```bash
docker build -t snexus-bot .
```

2. اجرا با داکر:
```bash
docker run -d --name snexus-bot --env-file config/.env snexus-bot
```

## ساختار پروژه

- `bot.py`: فایل اصلی برای اجرای ربات
- `config/`: تنظیمات و پیکربندی‌ها
- `database/`: کلاس‌های مرتبط با دیتابیس
- `handlers/`: پردازش‌کننده‌های دستورات تلگرام
- `models/`: مدل‌های داده
- `services/`: سرویس‌های مختلف مانند دانلود
- `utils/`: توابع کمکی

## مجوز

این پروژه تحت مجوز MIT منتشر شده است.
