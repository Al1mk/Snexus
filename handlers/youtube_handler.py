from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import os
import yt_dlp
from models.models import User, VIPSubscription, Song, DownloadHistory
from utils.helpers import create_download_dir, sanitize_filename, format_size, get_file_size
from config.config import DOWNLOAD_DIR, DAILY_DOWNLOAD_LIMIT_MB
import logging

logger = logging.getLogger(__name__)

async def youtube_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /youtube command."""
    # Check if URL is already in context (redirected from another handler)
    youtube_url = context.user_data.get('youtube_url')
    if youtube_url:
        del context.user_data['youtube_url']
        await process_youtube_url(update, context, youtube_url)
        return
    
    keyboard = [
        [
            InlineKeyboardButton("🎵 دانلود موزیک", callback_data="youtube_type_audio"),
            InlineKeyboardButton("🎬 دانلود ویدیو", callback_data="youtube_type_video")
        ],
        [
            InlineKeyboardButton("📋 دانلود پلی‌لیست", callback_data="youtube_type_playlist"),
        ],
        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="menu_main")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "لطفاً لینک ویدیو یا پلی‌لیست یوتیوب را ارسال کنید یا نوع دانلود را انتخاب کنید:",
        reply_markup=reply_markup
    )

async def process_youtube_url(update: Update, context: ContextTypes.DEFAULT_TYPE, url=None) -> None:
    """Process YouTube URL."""
    if url is None:
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
    
    # Validate YouTube URL
    if not ('youtube.com' in url or 'youtu.be' in url):
        await update.message.reply_text(
            "❌ لینک وارد شده معتبر نیست. لطفاً یک لینک یوتیوب معتبر وارد کنید."
        )
        return
    
    # Send initial message
    processing_message = await update.message.reply_text(
        "در حال دریافت اطلاعات ویدیو از یوتیوب...\n"
        "این عملیات ممکن است چند لحظه طول بکشد."
    )
    
    try:
        # Create download directory for user
        user_download_dir = create_download_dir(DOWNLOAD_DIR, user_id)
        
        # Get video info
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'format': 'best',
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Check if it's a playlist
            if 'entries' in info:
                # It's a playlist
                await processing_message.edit_text(
                    f"پلی‌لیست یافت شد: {info.get('title', 'بدون عنوان')}\n"
                    f"تعداد ویدیوها: {len(info['entries'])}\n\n"
                    "لطفاً نوع دانلود را انتخاب کنید:"
                )
                
                keyboard = [
                    [
                        InlineKeyboardButton("🎵 دانلود صوتی", callback_data=f"youtube_playlist_audio_{url}"),
                        InlineKeyboardButton("🎬 دانلود ویدیویی", callback_data=f"youtube_playlist_video_{url}")
                    ],
                    [InlineKeyboardButton("🔙 بازگشت", callback_data="menu_youtube")]
                ]
                
                await processing_message.edit_reply_markup(InlineKeyboardMarkup(keyboard))
            else:
                # It's a single video
                title = info.get('title', 'بدون عنوان')
                duration = info.get('duration', 0)
                duration_str = f"{duration // 60}:{duration % 60:02d}" if duration else "نامشخص"
                
                formats = []
                if info.get('formats'):
                    # Audio formats
                    audio_formats = [f for f in info['formats'] if f.get('acodec') != 'none' and f.get('vcodec') == 'none']
                    if audio_formats:
                        formats.append({
                            'id': 'audio',
                            'ext': 'mp3',
                            'quality': 'بهترین کیفیت صوتی',
                            'size_approx': next((f.get('filesize', 0) for f in audio_formats if f.get('filesize')), 0)
                        })
                    
                    # Video formats
                    video_formats = [f for f in info['formats'] if f.get('vcodec') != 'none' and f.get('height')]
                    video_formats.sort(key=lambda x: (x.get('height', 0), x.get('filesize', 0)), reverse=True)
                    
                    # Add top 3 video qualities
                    for i, fmt in enumerate(video_formats[:3]):
                        height = fmt.get('height', 0)
                        if height:
                            formats.append({
                                'id': f"video_{fmt['format_id']}",
                                'ext': fmt.get('ext', 'mp4'),
                                'quality': f"{height}p",
                                'size_approx': fmt.get('filesize', 0)
                            })
                
                # Create keyboard with format options
                keyboard = []
                for fmt in formats:
                    size_str = format_size(fmt['size_approx']) if fmt['size_approx'] else "نامشخص"
                    label = f"{fmt['quality']} ({size_str})"
                    callback_data = f"youtube_download_{fmt['id']}_{url}"
                    keyboard.append([InlineKeyboardButton(label, callback_data=callback_data)])
                
                keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="menu_youtube")])
                
                await processing_message.edit_text(
                    f"🎬 *{title}*\n"
                    f"⏱ مدت زمان: {duration_str}\n\n"
                    "لطفاً کیفیت مورد نظر را انتخاب کنید:",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='Markdown'
                )
    
    except Exception as e:
        logger.error(f"Error processing YouTube URL: {e}")
        await processing_message.edit_text(
            "❌ خطا در پردازش ویدیوی یوتیوب. لطفاً مجدداً تلاش کنید یا با پشتیبانی تماس بگیرید."
        )
