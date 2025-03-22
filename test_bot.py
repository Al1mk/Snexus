#!/usr/bin/env python3
import os
import sys
import logging
from dotenv import load_dotenv

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables from .env file
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config', '.env'))

from utils.helpers import setup_logger

# Setup logging
logger = setup_logger('test_bot', 'logs/test_bot.log')

def main():
    """Test bot functionality."""
    logger.info("Testing bot functionality...")
    
    # Import bot token
    from config.config import TELEGRAM_BOT_TOKEN
    
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "your_telegram_bot_token_here":
        logger.error("Telegram bot token not set in .env file")
        print("❌ Error: Telegram bot token not set in .env file")
        return False
    
    # Test database connection
    try:
        from database.db import Database
        db = Database()
        if not db.connection or not db.connection.is_connected():
            logger.error("Failed to connect to database")
            print("❌ Error: Failed to connect to database")
            return False
        logger.info("Database connection successful")
        print("✅ Database connection successful")
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        print(f"❌ Error: Database connection error: {e}")
        return False
    
    # Test model imports
    try:
        from models.models import User, VIPSubscription, Playlist, Song, DownloadHistory, RequiredChannel
        logger.info("Model imports successful")
        print("✅ Model imports successful")
    except Exception as e:
        logger.error(f"Model imports error: {e}")
        print(f"❌ Error: Model imports error: {e}")
        return False
    
    # Test handler imports
    try:
        from handlers.start_handler import start_handler, help_handler
        from handlers.music_handler import music_handler, process_music_url
        from handlers.youtube_handler import youtube_handler, process_youtube_url
        from handlers.instagram_handler import instagram_handler, process_instagram_url
        from handlers.playlist_handler import playlist_handler, create_playlist_handler, view_playlists_handler
        from handlers.vip_handler import vip_handler, process_vip_payment
        from handlers.admin_handler import admin_handler, broadcast_handler, channel_handler
        logger.info("Handler imports successful")
        print("✅ Handler imports successful")
    except Exception as e:
        logger.error(f"Handler imports error: {e}")
        print(f"❌ Error: Handler imports error: {e}")
        return False
    
    # Test telegram imports
    try:
        from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
        from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters
        logger.info("Telegram imports successful")
        print("✅ Telegram imports successful")
    except Exception as e:
        logger.error(f"Telegram imports error: {e}")
        print(f"❌ Error: Telegram imports error: {e}")
        return False
    
    logger.info("All tests passed successfully")
    print("✅ All tests passed successfully. The bot is ready to run.")
    return True

if __name__ == "__main__":
    main()
