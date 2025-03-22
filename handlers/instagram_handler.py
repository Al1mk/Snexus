from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import os
from models.models import User, VIPSubscription, DownloadHistory
from utils.helpers import create_download_dir, format_size, get_file_size
from config.config import DOWNLOAD_DIR, DAILY_DOWNLOAD_LIMIT_MB
from services.instagram_service import InstagramDownloadService
import logging

logger = logging.getLogger(__name__)

# Initialize Instagram download service
instagram_service = InstagramDownloadService()

async def instagram_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /instagram command."""
    keyboard = [
        [
            InlineKeyboardButton("📷 دانلود پست", callback_data="instagram_type_post"),
            InlineKeyboardButton("📱 دانلود ریلز", callback_data="instagram_type_reel")
        ],
        [
            InlineKeyboardButton("🔄 دانلود استوری", callback_data="instagram_type_story"),
            InlineKeyboardButton("👤 دانلود پروفایل", callback_data="instagram_type_profile")
        ],
        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="menu_main")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "لطفاً لینک پست، ریلز، استوری یا پروفایل اینستاگرام را ارسال کنید یا نوع دانلود را انتخاب کنید:",
        reply_markup=reply_markup
    )

async def process_instagram_url(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process Instagram URL."""
    url = update.message.text.strip()
    user_id = update.effective_user.id
    
    # Initialize database models
    db = context.bot_data.get('db')
    user_model = User(db)
    vip_model = VIPSubscription(db)
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
    
    # Validate Instagram URL
    if 'instagram.com' not in url:
        await update.message.reply_text(
            "❌ لینک وارد شده معتبر نیست. لطفاً یک لینک اینستاگرام معتبر ارسال کنید."
        )
        return
    
    # Determine content type from URL
    content_type = "post"  # Default
    if '/p/' in url:
        content_type = "post"
    elif '/reel/' in url:
        content_type = "reel"
    elif '/stories/' in url:
        content_type = "story"
    else:
        content_type = "profile"
    
    # Send initial message
    processing_message = await update.message.reply_text(
        f"در حال پردازش {content_type} از اینستاگرام...\n"
        "این عملیات ممکن است چند لحظه طول بکشد."
    )
    
    try:
        # Download content
        result = instagram_service.download_from_url(url, user_id, DOWNLOAD_DIR)
        
        if not result:
            await processing_message.edit_text(
                "❌ خطا در دانلود محتوا از اینستاگرام. لطفاً مجدداً تلاش کنید یا با پشتیبانی تماس بگیرید."
            )
            return
        
        # Process result based on type
        if result['type'] == 'photo':
            # Get file size
            file_size = get_file_size(result['file_path'])
            
            # Update user's download usage
            if file_size > 0:
                user_model.update_download_usage(user_id, file_size)
            
            # Add to download history
            download_model.add_download(
                user_id=user_id,
                content_type='instagram_photo',
                content_url=url,
                file_size=file_size
            )
            
            # Send the file
            await processing_message.edit_text(
                f"✅ عکس با موفقیت دانلود شد!\n\n"
                f"👤 کاربر: {result['owner']}\n"
                f"💾 حجم: {format_size(file_size)}\n\n"
                "در حال ارسال فایل..."
            )
            
            # Send photo
            with open(result['file_path'], 'rb') as photo_file:
                await update.message.reply_photo(
                    photo=photo_file,
                    caption=f"📷 پست اینستاگرام از {result['owner']}\n\n"
                            f"{result['caption'][:200] + '...' if len(result['caption']) > 200 else result['caption']}\n\n"
                            f"دانلود شده توسط ربات Snexus"
                )
            
            # Final message
            keyboard = [
                [InlineKeyboardButton("🔙 بازگشت به منوی اینستاگرام", callback_data="menu_instagram")]
            ]
            
            await processing_message.edit_text(
                f"✅ عکس با موفقیت دانلود شد!\n\n"
                f"👤 کاربر: {result['owner']}\n"
                f"💾 حجم: {format_size(file_size)}",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
        elif result['type'] == 'video' or result['type'] == 'reel':
            # Get file size
            file_size = get_file_size(result['file_path'])
            
            # Update user's download usage
            if file_size > 0:
                user_model.update_download_usage(user_id, file_size)
            
            # Add to download history
            download_model.add_download(
                user_id=user_id,
                content_type=f"instagram_{result['type']}",
                content_url=url,
                file_size=file_size
            )
            
            # Send the file
            await processing_message.edit_text(
                f"✅ ویدیو با موفقیت دانلود شد!\n\n"
                f"👤 کاربر: {result['owner']}\n"
                f"💾 حجم: {format_size(file_size)}\n\n"
                "در حال ارسال فایل..."
            )
            
            # Send video
            with open(result['file_path'], 'rb') as video_file:
                await update.message.reply_video(
                    video=video_file,
                    caption=f"🎬 {'ریلز' if result['type'] == 'reel' else 'ویدیو'} اینستاگرام از {result['owner']}\n\n"
                            f"{result['caption'][:200] + '...' if len(result['caption']) > 200 else result['caption']}\n\n"
                            f"دانلود شده توسط ربات Snexus"
                )
            
            # Send audio if available
            if 'audio_path' in result and result['audio_path']:
                with open(result['audio_path'], 'rb') as audio_file:
                    await update.message.reply_audio(
                        audio=audio_file,
                        title=f"Audio - {result['owner']} {'Reel' if result['type'] == 'reel' else 'Video'}",
                        performer=result['owner'],
                        caption=f"🎵 فایل صوتی {'ریلز' if result['type'] == 'reel' else 'ویدیو'} اینستاگرام از {result['owner']}\n\n"
                                f"دانلود شده توسط ربات Snexus"
                    )
            
            # Final message
            keyboard = [
                [InlineKeyboardButton("🔙 بازگشت به منوی اینستاگرام", callback_data="menu_instagram")]
            ]
            
            await processing_message.edit_text(
                f"✅ {'ریلز' if result['type'] == 'reel' else 'ویدیو'} با موفقیت دانلود شد!\n\n"
                f"👤 کاربر: {result['owner']}\n"
                f"💾 حجم: {format_size(file_size)}",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
        elif result['type'] == 'story':
            # Get file size
            file_size = get_file_size(result['file_path'])
            
            # Update user's download usage
            if file_size > 0:
                user_model.update_download_usage(user_id, file_size)
            
            # Add to download history
            download_model.add_download(
                user_id=user_id,
                content_type='instagram_story',
                content_url=url,
                file_size=file_size
            )
            
            # Send the file
            await processing_message.edit_text(
                f"✅ استوری با موفقیت دانلود شد!\n\n"
                f"👤 کاربر: {result['owner']}\n"
                f"💾 حجم: {format_size(file_size)}\n\n"
                "در حال ارسال فایل..."
            )
            
            # Send story (photo or video)
            if result['is_video']:
                with open(result['file_path'], 'rb') as video_file:
                    await update.message.reply_video(
                        video=video_file,
                        caption=f"🎬 استوری اینستاگرام از {result['owner']}\n\n"
                                f"دانلود شده توسط ربات Snexus"
                    )
                
                # Send audio if available
                if result['audio_path']:
                    with open(result['audio_path'], 'rb') as audio_file:
                        await update.message.reply_audio(
                            audio=audio_file,
                            title=f"Audio - {result['owner']} Story",
                            performer=result['owner'],
                            caption=f"🎵 فایل صوتی استوری اینستاگرام از {result['owner']}\n\n"
                                    f"دانلود شده توسط ربات Snexus"
                        )
            else:
                with open(result['file_path'], 'rb') as photo_file:
                    await update.message.reply_photo(
                        photo=photo_file,
                        caption=f"📷 استوری اینستاگرام از {result['owner']}\n\n"
                                f"دانلود شده توسط ربات Snexus"
                    )
            
            # Final message
            keyboard = [
                [InlineKeyboardButton("🔙 بازگشت به منوی اینستاگرام", callback_data="menu_instagram")]
            ]
            
            await processing_message.edit_text(
                f"✅ استوری با موفقیت دانلود شد!\n\n"
                f"👤 کاربر: {result['owner']}\n"
                f"💾 حجم: {format_size(file_size)}",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
        elif result['type'] == 'profile':
            # Get file size
            file_size = get_file_size(result['file_path'])
            
            # Update user's download usage
            if file_size > 0:
                user_model.update_download_usage(user_id, file_size)
            
            # Add to download history
            download_model.add_download(
                user_id=user_id,
                content_type='instagram_profile',
                content_url=url,
                file_size=file_size
            )
            
            # Send the file
            await processing_message.edit_text(
                f"✅ عکس پروفایل با موفقیت دانلود شد!\n\n"
                f"👤 کاربر: {result['username']}\n"
                f"📝 نام: {result['full_name']}\n"
                f"👥 دنبال‌کنندگان: {result['followers']}\n"
                f"💾 حجم: {format_size(file_size)}\n\n"
                "در حال ارسال فایل..."
            )
            
            # Send profile picture
            with open(result['file_path'], 'rb') as photo_file:
                await update.message.reply_photo(
                    photo=photo_file,
                    caption=f"👤 عکس پروفایل {result['username']} ({result['full_name']})\n\n"
                            f"👥 دنبال‌کنندگان: {result['followers']}\n"
                            f"👣 دنبال‌شوندگان: {result['followees']}\n\n"
                            f"📝 بیوگرافی: {result['biography'][:200] + '...' if len(result['biography']) > 200 else result['biography']}\n\n"
                            f"دانلود شده توسط ربات Snexus"
                )
            
            # Final message
            keyboard = [
                [InlineKeyboardButton("🔙 بازگشت به منوی اینستاگرام", callback_data="menu_instagram")]
            ]
            
            await processing_message.edit_text(
                f"✅ عکس پروفایل با موفقیت دانلود شد!\n\n"
                f"👤 کاربر: {result['username']}\n"
                f"📝 نام: {result['full_name']}\n"
                f"👥 دنبال‌کنندگان: {result['followers']}\n"
                f"💾 حجم: {format_size(file_size)}",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
    
    except Exception as e:
        logger.error(f"Error processing Instagram URL: {e}")
        await processing_message.edit_text(
            "❌ خطا در دانلود محتوا از اینستاگرام. لطفاً مجدداً تلاش کنید یا با پشتیبانی تماس بگیرید."
        )
