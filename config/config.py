import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "7700718557:AAF_UpYA8hi0BeIE54F0v8CeO62KAD2H6EI")
ADMIN_USER_IDS = list(map(int, os.getenv("ADMIN_USER_IDS", "").split(","))) if os.getenv("ADMIN_USER_IDS") else []

# Database Configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "snexus_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "snexus_db")

# Download Limits
DAILY_DOWNLOAD_LIMIT_MB = int(os.getenv("DAILY_DOWNLOAD_LIMIT_MB", 2048))  # 2GB in MB

# VIP Subscription Prices (in Toman)
ONE_MONTH_PRICE = int(os.getenv("ONE_MONTH_PRICE", 50000))
THREE_MONTH_PRICE = int(os.getenv("THREE_MONTH_PRICE", 140000))

# Payment Information
PAYMENT_CARD_NUMBER = os.getenv("PAYMENT_CARD_NUMBER", "")
PAYMENT_CARD_OWNER = os.getenv("PAYMENT_CARD_OWNER", "")

# Spotify API Credentials
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID", "")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", "")

# YouTube API Key (Optional)
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "")

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# File paths
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
DOWNLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "downloads")

# Create directories if they don't exist
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Maximum number of required channels to join
MAX_REQUIRED_CHANNELS = 5
