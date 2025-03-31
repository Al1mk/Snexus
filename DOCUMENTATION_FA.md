# Snexus Telegram Bot - راهنمای فارسی

## مرور کلی
این سند اطلاعاتی درباره ربات تلگرام Snexus، تغییرات انجام شده برای رفع مشکلات، و دستورالعمل‌هایی برای نگهداری و توسعه آینده ارائه می‌دهد.

## مشکلات رفع شده
1. **عملکرد دکمه‌ها**: ناهماهنگی‌های بین bot.py و main.py که باعث مشکلات عملکرد دکمه‌ها می‌شد، رفع شد
2. **توابع منو**: تمام توابع منو به درستی پیاده‌سازی شدند تا ناوبری صحیح تضمین شود
3. **مدیریت کننده Callback**: یک پیاده‌سازی یکپارچه از مدیریت کننده callback ایجاد شد
4. **راه‌اندازی محیط**: فایل .env مناسب با پیکربندی برای اطلاعات احراز هویت API ایجاد شد
5. **راه‌اندازی پایگاه داده**: اطمینان از راه‌اندازی و اتصال صحیح پایگاه داده

## ساختار پروژه
- **bot_unified.py**: فایل اصلی ربات که عملکرد هر دو فایل bot.py و main.py را ترکیب می‌کند
- **config/**: شامل فایل‌های پیکربندی از جمله config.py
- **database/**: شامل فایل‌های مرتبط با پایگاه داده از جمله db.py و setup_db.py
- **handlers/**: شامل توابع مدیریت کننده برای دستورات و ویژگی‌های مختلف
- **models/**: شامل مدل‌های پایگاه داده برای موجودیت‌های مختلف
- **services/**: شامل توابع سرویس برای API‌های خارجی
- **utils/**: شامل توابع کمکی
- **.env**: شامل متغیرهای محیطی و اطلاعات احراز هویت API

## دستورالعمل‌های راه‌اندازی
1. کلون کردن مخزن:
   ```
   git clone https://github.com/Al1mk/Snexus.git
   ```

2. نصب وابستگی‌ها:
   ```
   pip3 install -r requirements.txt
   ```

3. ایجاد فایل .env با محتوای زیر:
   ```
   # Telegram Bot Configuration
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token
   ADMIN_USER_IDS=your_admin_user_id

   # Database Configuration
   DB_HOST=localhost
   DB_USER=snexus_user
   DB_PASSWORD=your_db_password
   DB_NAME=snexus_db

   # Download Limits
   DAILY_DOWNLOAD_LIMIT_MB=2048  # 2GB in MB

   # VIP Subscription Prices (in Toman)
   ONE_MONTH_PRICE=50000
   THREE_MONTH_PRICE=140000

   # Payment Information
   PAYMENT_CARD_NUMBER=
   PAYMENT_CARD_OWNER=

   # Spotify API Credentials
   SPOTIFY_CLIENT_ID=your_spotify_client_id
   SPOTIFY_CLIENT_SECRET=your_spotify_client_secret

   # YouTube API Key (Optional)
   YOUTUBE_API_KEY=your_youtube_api_key

   # Logging Configuration
   LOG_LEVEL=INFO
   ```

4. راه‌اندازی پایگاه داده MySQL:
   ```
   sudo mysql -e "CREATE DATABASE IF NOT EXISTS snexus_db; CREATE USER IF NOT EXISTS 'snexus_user'@'localhost' IDENTIFIED BY 'your_db_password'; GRANT ALL PRIVILEGES ON snexus_db.* TO 'snexus_user'@'localhost'; FLUSH PRIVILEGES;"
   ```

5. مقداردهی اولیه پایگاه داده:
   ```
   python3 database/setup_db.py
   ```

6. اجرای ربات:
   ```
   python3 bot_unified.py
   ```

## اطلاعات احراز هویت API
ربات به اطلاعات احراز هویت API برای سرویس‌های زیر نیاز دارد:

1. **Spotify API**:
   - ثبت نام در [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/)
   - ایجاد یک برنامه جدید
   - استفاده از http://localhost:8888/callback به عنوان Redirect URI
   - دریافت Client ID و Client Secret

2. **YouTube API**:
   - ثبت نام در [Google Cloud Console](https://console.cloud.google.com/)
   - ایجاد یک پروژه جدید
   - فعال کردن YouTube Data API v3
   - ایجاد اطلاعات احراز هویت API و دریافت API Key

## اجرا به عنوان یک سرویس
برای اجرای ربات به عنوان یک سرویس که به طور خودکار در هنگام راه‌اندازی سیستم شروع می‌شود:

1. ایجاد یک فایل سرویس systemd:
   ```
   sudo nano /etc/systemd/system/snexus-bot.service
   ```

2. افزودن محتوای زیر:
   ```
   [Unit]
   Description=Snexus Telegram Bot
   After=network.target

   [Service]
   User=your_username
   WorkingDirectory=/path/to/Snexus
   ExecStart=/usr/bin/python3 /path/to/Snexus/bot_unified.py
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   ```

3. فعال‌سازی و شروع سرویس:
   ```
   sudo systemctl enable snexus-bot.service
   sudo systemctl start snexus-bot.service
   ```

4. بررسی وضعیت:
   ```
   sudo systemctl status snexus-bot.service
   ```

## نگهداری
1. **لاگ‌ها**: دایرکتوری logs را برای لاگ‌های خطا بررسی کنید
2. **پشتیبان‌گیری از پایگاه داده**: به طور منظم از پایگاه داده MySQL پشتیبان‌گیری کنید
3. **اطلاعات احراز هویت API**: اطلاعات احراز هویت API را به روز نگه دارید
4. **وابستگی‌ها**: وابستگی‌ها را به طور منظم به روز کنید تا امنیت و عملکرد تضمین شود

## عیب‌یابی
1. **ربات پاسخ نمی‌دهد**: بررسی کنید که آیا فرآیند ربات در حال اجراست و لاگ‌ها را بررسی کنید
2. **مشکلات اتصال به پایگاه داده**: تأیید کنید که MySQL در حال اجراست و اطلاعات احراز هویت صحیح هستند
3. **خطاهای API**: تأیید کنید که اطلاعات احراز هویت API معتبر هستند و منقضی نشده‌اند
4. **مشکلات عملکرد دکمه‌ها**: اطمینان حاصل کنید که مدیریت کننده callback به درستی پیاده‌سازی شده است

## بهبودهای آینده
1. **مدیریت خطا**: بهبود مدیریت خطا برای تجربه کاربری بهتر
2. **کش کردن**: پیاده‌سازی کش برای داده‌های با دسترسی مکرر
3. **تجزیه و تحلیل**: افزودن تجزیه و تحلیل برای پیگیری رفتار کاربر و عملکرد ربات
4. **پشتیبانی از چند زبان**: افزودن پشتیبانی برای زبان‌های متعدد
5. **یکپارچه‌سازی پرداخت**: یکپارچه‌سازی با درگاه‌های پرداخت برای اشتراک‌های VIP
