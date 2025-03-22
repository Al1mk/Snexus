import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

from config.config import TELEGRAM_BOT_TOKEN, LOG_DIR
from utils.helpers import setup_logger
from database.db import Database
from models.models import User, VIPSubscription, Playlist, Song, DownloadHistory, RequiredChannel
from handlers.start_handler import start_handler, help_handler
from handlers.music_handler import music_handler, process_music_url
from handlers.youtube_handler import youtube_handler, process_youtube_url
from handlers.instagram_handler import instagram_handler, process_instagram_url
from handlers.playlist_handler import playlist_handler, create_playlist_handler, view_playlists_handler
from handlers.vip_handler import vip_handler, process_vip_payment
from handlers.admin_handler import admin_handler, broadcast_handler, channel_handler

# Setup logging
logger = setup_logger('bot', os.path.join(LOG_DIR, 'bot.log'))

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors caused by updates."""
    logger.error(f"Update {update} caused error {context.error}")

def main():
    """Start the bot."""
    # Initialize database
    db = Database()
    db.connect()
    
    # Create tables if they don't exist
    if not db.create_tables():
        logger.error("Failed to create database tables. Exiting...")
        return
    
    # Initialize models
    user_model = User(db)
    vip_model = VIPSubscription(db)
    playlist_model = Playlist(db)
    song_model = Song(db)
    download_model = DownloadHistory(db)
    channel_model = RequiredChannel(db)
    
    # Create application
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("help", help_handler))
    
    # Music download handlers
    application.add_handler(CommandHandler("music", music_handler))
    application.add_handler(MessageHandler(filters.Regex(r'(spotify\.com|music\.apple\.com|soundcloud\.com)'), process_music_url))
    
    # YouTube download handlers
    application.add_handler(CommandHandler("youtube", youtube_handler))
    application.add_handler(MessageHandler(filters.Regex(r'(youtube\.com|youtu\.be)'), process_youtube_url))
    
    # Instagram download handlers
    application.add_handler(CommandHandler("instagram", instagram_handler))
    application.add_handler(MessageHandler(filters.Regex(r'instagram\.com'), process_instagram_url))
    
    # Playlist handlers
    application.add_handler(CommandHandler("playlist", playlist_handler))
    application.add_handler(CommandHandler("create_playlist", create_playlist_handler))
    application.add_handler(CommandHandler("my_playlists", view_playlists_handler))
    
    # VIP subscription handlers
    application.add_handler(CommandHandler("vip", vip_handler))
    
    # Admin handlers
    application.add_handler(CommandHandler("admin", admin_handler))
    application.add_handler(CommandHandler("broadcast", broadcast_handler))
    application.add_handler(CommandHandler("channels", channel_handler))
    
    # Callback query handler for button clicks
    application.add_handler(CallbackQueryHandler(callback_handler))
    
    # Error handler
    application.add_error_handler(error_handler)
    
    # Start the Bot
    logger.info("Starting bot...")
    application.run_polling()

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle callback queries from inline keyboards."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data.startswith('music_'):
        # Handle music-related callbacks
        pass
    elif data.startswith('youtube_'):
        # Handle YouTube-related callbacks
        pass
    elif data.startswith('instagram_'):
        # Handle Instagram-related callbacks
        pass
    elif data.startswith('playlist_'):
        # Handle playlist-related callbacks
        pass
    elif data.startswith('vip_'):
        # Handle VIP-related callbacks
        if data == 'vip_1month':
            await process_vip_payment(update, context, 'one_month')
        elif data == 'vip_3month':
            await process_vip_payment(update, context, 'three_month')
    elif data.startswith('admin_'):
        # Handle admin-related callbacks
        pass

if __name__ == '__main__':
    main()
