from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import os
from models.models import User, VIPSubscription, Song, DownloadHistory
from utils.helpers import extract_platform_from_url, is_playlist_url, create_download_dir, format_size, get_file_size
from config.config import DOWNLOAD_DIR, DAILY_DOWNLOAD_LIMIT_MB
from services.music_service import MusicDownloadService
import logging

logger = logging.getLogger(__name__)

# Initialize music download service
music_service = MusicDownloadService()

async def music_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /music command."""
    keyboard = [
        [
            InlineKeyboardButton("Spotify", callback_data="music_platform_spotify"),
            InlineKeyboardButton("Apple Music", callback_data="music_platform_apple")
        ],
        [
            InlineKeyboardButton("SoundCloud", callback_data="music_platform_soundcloud"),
            InlineKeyboardButton("YouTube Music", callback_data="music_platform_youtube_music")
        ],
        [
            InlineKeyboardButton("🔥 آهنگ‌های محبوب", callback_data="music_popular"),
            InlineKeyboardButton("🆕 آهنگ‌های جدید", callback_data="music_new")
        ],
        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="menu_main")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "لطفاً پلتفرم موسیقی مورد نظر خود را انتخاب کنید یا لینک آهنگ/پلی‌لیست را مستقیماً ارسال کنید:",
        reply_markup=reply_markup
    )

async def process_music_url(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process music URL from various platforms."""
    url = update.message.text.strip()
    user_id = update.effective_user.id
    
    # Initialize database models
    db = context.bot_data.get('db')
    user_model = User(db)
    vip_model = VIPSubscription(db)
    song_model = Song(db)
    download_model = DownloadHistory(db)
    
    # Check if user exists
    user_data = user_model.get_user(user_id)
    if not user_data:
        user_model.create_user(
            user_id=user_id,
            username=update.effective_user.username,
            first_name=update.effective_user.first_name,
            last_name=update.effective_user.last_name
        )
    
    # Check download limits for non-VIP users
    is_vip = vip_model.is_vip(user_id)
    if not is_vip:
        usage = user_model.get_download_usage(user_id)
        if usage and usage['current_usage'] and usage['current_usage'] >= DAILY_DOWNLOAD_LIMIT_MB * 1024 * 1024:
            vip_keyboard = [
                [InlineKeyboardButton("خرید اشتراک VIP", callback_data="menu_vip")],
                [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="menu_main")]
            ]
            await update.message.reply_text(
                "⚠️ شما به محدودیت دانلود روزانه (۲ گیگابایت) رسیده‌اید.\n"
                "برای دانلود نامحدود، اشتراک VIP تهیه کنید.",
                reply_markup=InlineKeyboardMarkup(vip_keyboard)
            )
            return
    
    # Extract platform from URL
    platform = extract_platform_from_url(url)
    
    if not platform or platform == 'other':
        await update.message.reply_text(
            "❌ لینک وارد شده معتبر نیست یا از پلتفرم‌های پشتیبانی شده نمی‌باشد.\n"
            "پلتفرم‌های پشتیبانی شده: Spotify، Apple Music، SoundCloud، YouTube Music"
        )
        return
    
    # Check if it's a playlist
    is_playlist = is_playlist_url(url, platform)
    
    # Send initial message
    processing_message = await update.message.reply_text(
        f"در حال پردازش {'پلی‌لیست' if is_playlist else 'آهنگ'} از {platform}...\n"
        "این عملیات ممکن است چند لحظه طول بکشد."
    )
    
    try:
        # Download music
        result = music_service.download_from_url(url, user_id, DOWNLOAD_DIR)
        
        if not result:
            await processing_message.edit_text(
                "❌ خطا در دانلود موسیقی. لطفاً مجدداً تلاش کنید یا با پشتیبانی تماس بگیرید."
            )
            return
        
        # Process result based on type
        if result['type'] == 'track':
            # Get file size
            file_size = get_file_size(result['file_path'])
            
            # Update user's download usage
            if file_size > 0:
                user_model.update_download_usage(user_id, file_size)
            
            # Add to download history
            download_model.add_download(
                user_id=user_id,
                content_type='music',
                content_url=url,
                file_size=file_size
            )
            
            # Check if song exists in database
            existing_song = song_model.get_song_by_url(url)
            if existing_song:
                # Update download count
                song_model.increment_download_count(existing_song['id'])
                song_id = existing_song['id']
            else:
                # Add song to database
                song_id = song_model.create_song(
                    title=result['name'],
                    artist=result['artist'],
                    platform=platform,
                    url=url,
                    file_path=result['file_path'],
                    language='other'  # Default language
                )
            
            # Send the file
            await processing_message.edit_text(
                f"✅ آهنگ با موفقیت دانلود شد!\n\n"
                f"🎵 نام: {result['name']}\n"
                f"👤 هنرمند: {result['artist']}\n"
                f"💾 حجم: {format_size(file_size)}\n\n"
                "در حال ارسال فایل..."
            )
            
            # Send audio file
            with open(result['file_path'], 'rb') as audio_file:
                await update.message.reply_audio(
                    audio=audio_file,
                    title=result['name'],
                    performer=result['artist'],
                    caption=f"🎵 {result['name']} - {result['artist']}\n\nدانلود شده توسط ربات Snexus"
                )
            
            # Add to playlist button
            keyboard = [
                [InlineKeyboardButton("➕ افزودن به پلی‌لیست", callback_data=f"add_to_playlist_{song_id}")],
                [InlineKeyboardButton("🔙 بازگشت به منوی موسیقی", callback_data="menu_music")]
            ]
            
            await processing_message.edit_text(
                f"✅ آهنگ با موفقیت دانلود شد!\n\n"
                f"🎵 نام: {result['name']}\n"
                f"👤 هنرمند: {result['artist']}\n"
                f"💾 حجم: {format_size(file_size)}",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
        elif result['type'] == 'playlist':
            # Process playlist
            total_size = 0
            for track in result['tracks']:
                file_size = get_file_size(track['file_path'])
                total_size += file_size
                
                # Add song to database
                existing_song = song_model.get_song_by_url(url + f"/{track['name']}")  # Approximate URL
                if not existing_song:
                    song_model.create_song(
                        title=track['name'],
                        artist=track['artist'],
                        platform=platform,
                        url=url + f"/{track['name']}",  # Approximate URL
                        file_path=track['file_path'],
                        language='other'  # Default language
                    )
            
            # Update user's download usage
            if total_size > 0:
                user_model.update_download_usage(user_id, total_size)
            
            # Add to download history
            download_model.add_download(
                user_id=user_id,
                content_type='music',
                content_url=url,
                file_size=total_size
            )
            
            # Send message with playlist info
            await processing_message.edit_text(
                f"✅ پلی‌لیست با موفقیت دانلود شد!\n\n"
                f"🎵 نام پلی‌لیست: {result['name']}\n"
                f"🔢 تعداد آهنگ‌ها: {len(result['tracks'])}/{result['tracks_count']}\n"
                f"💾 حجم کل: {format_size(total_size)}\n\n"
                "در حال ارسال فایل‌ها..."
            )
            
            # Send audio files
            for track in result['tracks']:
                with open(track['file_path'], 'rb') as audio_file:
                    await update.message.reply_audio(
                        audio=audio_file,
                        title=track['name'],
                        performer=track['artist'],
                        caption=f"🎵 {track['name']} - {track['artist']}\n\nاز پلی‌لیست {result['name']}\nدانلود شده توسط ربات Snexus"
                    )
            
            # Create playlist button
            keyboard = [
                [InlineKeyboardButton("➕ ایجاد پلی‌لیست از این آهنگ‌ها", callback_data=f"create_playlist_from_{url}")],
                [InlineKeyboardButton("🔙 بازگشت به منوی موسیقی", callback_data="menu_music")]
            ]
            
            await processing_message.edit_text(
                f"✅ پلی‌لیست با موفقیت دانلود شد!\n\n"
                f"🎵 نام پلی‌لیست: {result['name']}\n"
                f"🔢 تعداد آهنگ‌ها: {len(result['tracks'])}/{result['tracks_count']}\n"
                f"💾 حجم کل: {format_size(total_size)}",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
    
    except Exception as e:
        logger.error(f"Error processing music URL: {e}")
        await processing_message.edit_text(
            "❌ خطا در دانلود موسیقی. لطفاً مجدداً تلاش کنید یا با پشتیبانی تماس بگیرید."
        )
