#!/usr/bin/env python3
import os
import logging
import sys
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.config import TELEGRAM_BOT_TOKEN, LOG_DIR, ADMIN_USER_IDS
from utils.helpers import setup_logger
from database.db import Database
from models.models import User, VIPSubscription, Playlist, Song, DownloadHistory, RequiredChannel
from handlers.start_handler import start_handler, help_handler
from handlers.music_handler import music_handler, process_music_url
from handlers.youtube_handler import youtube_handler, process_youtube_url
from handlers.instagram_handler import instagram_handler, process_instagram_url
from handlers.playlist_handler import playlist_handler, create_playlist_handler, view_playlists_handler
from handlers.vip_handler import vip_handler, process_vip_payment
from handlers.admin_handler import admin_handler, broadcast_handler, channel_handler, process_broadcast

# Setup logging
os.makedirs(LOG_DIR, exist_ok=True)
logger = setup_logger('bot', os.path.join(LOG_DIR, 'bot.log'))

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors caused by updates."""
    logger.error(f"Update {update} caused error {context.error}")

async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle callback queries from inline keyboards."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "menu_main":
        # Return to main menu
        keyboard = [
            [
                InlineKeyboardButton("🎵 دانلود موزیک", callback_data="menu_music"),
                InlineKeyboardButton("🎬 دانلود از یوتیوب", callback_data="menu_youtube")
            ],
            [
                InlineKeyboardButton("📱 دانلود از اینستاگرام", callback_data="menu_instagram"),
                InlineKeyboardButton("📋 پلی‌لیست‌های من", callback_data="menu_playlists")
            ],
            [
                InlineKeyboardButton("⭐️ اشتراک VIP", callback_data="menu_vip"),
                InlineKeyboardButton("❓ راهنما", callback_data="menu_help")
            ]
        ]
        
        # Add admin button if user is admin
        user_id = update.effective_user.id
        db = context.bot_data.get('db')
        user_model = User(db)
        
        if user_id in ADMIN_USER_IDS or (user_model and user_model.is_admin(user_id)):
            keyboard.append([InlineKeyboardButton("🔐 پنل مدیریت", callback_data="menu_admin")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.edit_text(
            f"سلام {update.effective_user.first_name}! به ربات Snexus خوش آمدید.\n\n"
            "با این ربات می‌توانید:\n"
            "• موزیک از پلتفرم‌های مختلف دانلود کنید\n"
            "• ویدیو از یوتیوب دانلود کنید\n"
            "• محتوا از اینستاگرام دانلود کنید\n"
            "• پلی‌لیست‌های شخصی بسازید\n\n"
            "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
            reply_markup=reply_markup
        )
    
    elif data == "menu_music":
        # Show music menu
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
        
        await query.message.edit_text(
            "لطفاً پلتفرم موسیقی مورد نظر خود را انتخاب کنید یا لینک آهنگ/پلی‌لیست را مستقیماً ارسال کنید:",
            reply_markup=reply_markup
        )
    
    elif data == "menu_youtube":
        # Show YouTube menu
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
        
        await query.message.edit_text(
            "لطفاً لینک ویدیو یا پلی‌لیست یوتیوب را ارسال کنید یا نوع دانلود را انتخاب کنید:",
            reply_markup=reply_markup
        )
    
    elif data == "menu_instagram":
        # Show Instagram menu
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
        
        await query.message.edit_text(
            "لطفاً لینک پست، ریلز، استوری یا پروفایل اینستاگرام را ارسال کنید یا نوع دانلود را انتخاب کنید:",
            reply_markup=reply_markup
        )
    
    elif data == "menu_playlists":
        # Show playlists menu
        user_id = update.effective_user.id
        
        # Initialize database models
        db = context.bot_data.get('db')
        playlist_model = Playlist(db)
        
        # Get user's playlists
        playlists = playlist_model.get_user_playlists(user_id)
        
        keyboard = [
            [InlineKeyboardButton("➕ ایجاد پلی‌لیست جدید", callback_data="playlist_create")],
        ]
        
        # Add user's playlists to keyboard
        if playlists:
            for playlist in playlists:
                keyboard.append([
                    InlineKeyboardButton(
                        f"🎵 {playlist['name']} ({playlist['id']})", 
                        callback_data=f"playlist_view_{playlist['id']}"
                    )
                ])
        
        keyboard.append([InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="menu_main")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.message.edit_text(
            "🎵 *مدیریت پلی‌لیست‌ها*\n\n"
            "در این بخش می‌توانید پلی‌لیست‌های خود را مدیریت کنید، "
            "آهنگ‌های مورد علاقه خود را به آن‌ها اضافه کنید و آن‌ها را با دوستان خود به اشتراک بگذارید.\n\n"
            "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    elif data == "menu_vip":
        # Show VIP subscription menu
        user_id = update.effective_user.id
        
        # Initialize database models
        db = context.bot_data.get('db')
        vip_model = VIPSubscription(db)
        
        # Check if user has active subscription
        subscription = vip_model.get_active_subscription(user_id)
        
        if subscription:
            # User has active subscription
            end_date = subscription['end_date'].strftime('%Y-%m-%d')
            
            keyboard = [
                [InlineKeyboardButton("تمدید اشتراک", callback_data="menu_vip_extend")],
                [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="menu_main")]
            ]
            
            await query.message.edit_text(
                f"✅ *اشتراک VIP شما فعال است*\n\n"
                f"تاریخ پایان اشتراک: {end_date}\n\n"
                "با اشتراک VIP شما می‌توانید:\n"
                "• بدون محدودیت دانلود کنید\n"
                "• به تمام قابلیت‌های ربات دسترسی داشته باشید\n"
                "• پلی‌لیست‌های نامحدود بسازید\n",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
        else:
            # User doesn't have active subscription
            from config.config import ONE_MONTH_PRICE, THREE_MONTH_PRICE
            
            keyboard = [
                [
                    InlineKeyboardButton(f"یک ماهه ({ONE_MONTH_PRICE} تومان)", callback_data="vip_1month"),
                    InlineKeyboardButton(f"سه ماهه ({THREE_MONTH_PRICE} تومان)", callback_data="vip_3month")
                ],
                [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="menu_main")]
            ]
            
            await query.message.edit_text(
                "⭐️ *اشتراک VIP*\n\n"
                "با خرید اشتراک VIP می‌توانید:\n"
                "• بدون محدودیت دانلود کنید (بدون سقف ۲ گیگابایت روزانه)\n"
                "• به تمام قابلیت‌های ربات دسترسی داشته باشید\n"
                "• پلی‌لیست‌های نامحدود بسازید\n\n"
                "لطفاً نوع اشتراک مورد نظر خود را انتخاب کنید:",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
    
    elif data == "menu_help":
        # Show help menu
        help_text = (
            "🔹 *راهنمای استفاده از ربات Snexus* 🔹\n\n"
            "*دانلود موزیک:*\n"
            "• لینک آهنگ یا پلی‌لیست از Spotify، Apple Music یا SoundCloud را ارسال کنید\n"
            "• یا از دکمه «دانلود موزیک» استفاده کنید\n\n"
            
            "*دانلود از یوتیوب:*\n"
            "• لینک ویدیو یا پلی‌لیست یوتیوب را ارسال کنید\n"
            "• کیفیت مورد نظر را انتخاب کنید\n\n"
            
            "*دانلود از اینستاگرام:*\n"
            "• لینک پست، ریلز، استوری یا پروفایل را ارسال کنید\n\n"
            
            "*مدیریت پلی‌لیست:*\n"
            "• با دستور /create_playlist پلی‌لیست جدید بسازید\n"
            "• با دستور /my_playlists پلی‌لیست‌های خود را مشاهده کنید\n"
            "• آهنگ‌ها را به پلی‌لیست اضافه کنید\n\n"
            
            "*اشتراک VIP:*\n"
            "• کاربران عادی: محدودیت دانلود روزانه 2 گیگابایت\n"
            "• کاربران VIP: دانلود نامحدود و دسترسی به تمام قابلیت‌ها\n"
            "• برای خرید اشتراک از دکمه «اشتراک VIP» استفاده کنید\n\n"
            
            "*دستورات مفید:*\n"
            "/start - شروع مجدد ربات\n"
            "/help - نمایش این راهنما\n"
            "/music - منوی دانلود موزیک\n"
            "/youtube - منوی دانلود از یوتیوب\n"
            "/instagram - منوی دانلود از اینستاگرام\n"
            "/playlist - منوی مدیریت پلی‌لیست\n"
            "/vip - اطلاعات و خرید اشتراک VIP"
        )
        
        keyboard = [[InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="menu_main")]]
        
        await query.message.edit_text(
            help_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    elif data == "menu_admin":
        # Show admin panel
        user_id = update.effective_user.id
        
        # Initialize database models
        db = context.bot_data.get('db')
        user_model = User(db)
        
        # Check if user is admin
        if user_id not in ADMIN_USER_IDS and not user_model.is_admin(user_id):
            await query.message.edit_text(
                "⛔️ شما دسترسی به پنل مدیریت را ندارید.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="menu_main")]])
            )
            return
        
        keyboard = [
            [
                InlineKeyboardButton("📢 ارسال پیام همگانی", callback_data="admin_broadcast"),
                InlineKeyboardButton("📤 فوروارد پیام همگانی", callback_data="admin_forward")
            ],
            [
                InlineKeyboardButton("📊 آمار ربات", callback_data="admin_stats"),
                InlineKeyboardButton("👥 مدیریت کاربران", callback_data="admin_users")
            ],
            [
                InlineKeyboardButton("📡 مدیریت کانال‌های اجباری", callback_data="admin_channels"),
                InlineKeyboardButton("💳 مدیریت پرداخت‌ها", callback_data="admin_payments")
            ],
            [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="menu_main")]
        ]
        
        await query.message.edit_text(
            "🔐 *پنل مدیریت*\n\n"
            "به پنل مدیریت ربات خوش آمدید. لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    elif data == "check_membership":
        # Check if user has joined required channels
        db = context.bot_data.get('db')
        channel_model = RequiredChannel(db)
        required_channels = channel_model.get_all_channels()
        
        if required_channels:
            all_joined = True
            channels_keyboard = []
            
            for channel in required_channels:
                try:
                    member = await context.bot.get_chat_member(chat_id=channel['channel_id'], user_id=update.effective_user.id)
                    if member.status in ['left', 'kicked', 'restricted']:
                        all_joined = False
                        channels_keyboard.append([
                            InlineKeyboardButton(text=f"عضویت در {channel['channel_name']}", url=channel['channel_url'])
                        ])
                except Exception as e:
                    logger.error(f"Error checking membership: {e}")
                    continue
            
            if not all_joined:
                channels_keyboard.append([InlineKeyboardButton(text="بررسی مجدد عضویت", callback_data="check_membership")])
                reply_markup = InlineKeyboardMarkup(channels_keyboard)
                
                await query.message.edit_text(
                    "برای استفاده از ربات، لطفا در کانال‌های زیر عضو شوید:",
                    reply_markup=reply_markup
                )
            else:
                # User has joined all channels, show main menu
                await query.message.edit_text("✅ عضویت شما در تمام کانال‌ها تأیید شد. در حال انتقال به منوی اصلی...")
                data = "menu_main"
                # Call this function again with menu_main
                await callback_handler(update, context)
        else:
            # No required channels, show main menu
            data = "menu_main"
            await callback_handler(update, context)

def main():
    """Start the bot."""
    # Initialize database
    db = Database()
    db.connect()
    
    # Create application
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Store database connection in bot_data
    application.bot_data['db'] = db
    
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

if __name__ == '__main__':
    main()
