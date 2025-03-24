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
    
    # Store models in bot_data for access in handlers
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    application.bot_data['db'] = db
    application.bot_data['user_model'] = user_model
    application.bot_data['vip_model'] = vip_model
    application.bot_data['playlist_model'] = playlist_model
    application.bot_data['song_model'] = song_model
    application.bot_data['download_model'] = download_model
    application.bot_data['channel_model'] = channel_model
    
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
    logger.info(f"Callback query received: {data}")
    
    # Main menu navigation
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
        user_model = context.bot_data.get('user_model')
        if user_model and user_model.is_admin(update.effective_user.id):
            keyboard.append([InlineKeyboardButton("🔐 پنل مدیریت", callback_data="menu_admin")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"سلام {update.effective_user.first_name}! به ربات Snexus خوش آمدید.\n\n"
            "با این ربات می‌توانید:\n"
            "• موزیک از پلتفرم‌های مختلف دانلود کنید\n"
            "• ویدیو از یوتیوب دانلود کنید\n"
            "• محتوا از اینستاگرام دانلود کنید\n"
            "• پلی‌لیست‌های شخصی بسازید\n\n"
            "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
            reply_markup=reply_markup
        )
    
    # Feature menu navigation
    elif data == "menu_music":
        # Show music download menu
        await music_menu(update, context)
    elif data == "menu_youtube":
        # Show YouTube download menu
        await youtube_menu(update, context)
    elif data == "menu_instagram":
        # Show Instagram download menu
        await instagram_menu(update, context)
    elif data == "menu_playlists":
        # Show playlists menu
        await playlists_menu(update, context)
    elif data == "menu_vip":
        # Show VIP subscription menu
        await vip_menu(update, context)
    elif data == "menu_help":
        # Show help menu
        await help_menu(update, context)
    elif data == "menu_admin":
        # Show admin menu
        await admin_menu(update, context)
    
    # Instagram specific callbacks
    elif data.startswith('instagram_type_'):
        content_type = data.replace('instagram_type_', '')
        await instagram_type_selected(update, context, content_type)
    
    # Music specific callbacks
    elif data.startswith('music_'):
        # Handle music-related callbacks
        if data == 'music_spotify':
            await query.edit_message_text(
                "لطفاً لینک آهنگ یا پلی‌لیست Spotify را ارسال کنید.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="menu_music")]])
            )
        elif data == 'music_apple':
            await query.edit_message_text(
                "لطفاً لینک آهنگ یا پلی‌لیست Apple Music را ارسال کنید.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="menu_music")]])
            )
        elif data == 'music_soundcloud':
            await query.edit_message_text(
                "لطفاً لینک آهنگ یا پلی‌لیست SoundCloud را ارسال کنید.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="menu_music")]])
            )
    
    # YouTube specific callbacks
    elif data.startswith('youtube_'):
        # Handle YouTube-related callbacks
        if data == 'youtube_video':
            await query.edit_message_text(
                "لطفاً لینک ویدیوی یوتیوب را ارسال کنید.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="menu_youtube")]])
            )
        elif data == 'youtube_playlist':
            await query.edit_message_text(
                "لطفاً لینک پلی‌لیست یوتیوب را ارسال کنید.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="menu_youtube")]])
            )
        elif data == 'youtube_audio':
            await query.edit_message_text(
                "لطفاً لینک ویدیوی یوتیوب را برای استخراج صدا ارسال کنید.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="menu_youtube")]])
            )
    
    # Playlist specific callbacks
    elif data.startswith('playlist_'):
        # Handle playlist-related callbacks
        playlist_id = data.replace('playlist_view_', '')
        if data.startswith('playlist_view_'):
            # View specific playlist
            await view_playlist(update, context, playlist_id)
        elif data == 'playlist_create':
            await query.edit_message_text(
                "برای ساخت پلی‌لیست جدید، لطفاً از دستور /create_playlist استفاده کنید و نام پلی‌لیست را وارد کنید.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="menu_playlists")]])
            )
    
    # VIP specific callbacks
    elif data.startswith('vip_'):
        # Handle VIP-related callbacks
        if data == 'vip_1month':
            await process_vip_payment(update, context, 'one_month')
        elif data == 'vip_3month':
            await process_vip_payment(update, context, 'three_month')
    
    # Admin specific callbacks
    elif data.startswith('admin_'):
        # Handle admin-related callbacks
        if data == 'admin_broadcast':
            await query.edit_message_text(
                "برای ارسال پیام به همه کاربران، لطفاً از دستور /broadcast استفاده کنید و متن پیام را وارد کنید.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="menu_admin")]])
            )
        elif data == 'admin_channels':
            await query.edit_message_text(
                "برای مدیریت کانال‌های اجباری، لطفاً از دستور /channels استفاده کنید.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="menu_admin")]])
            )
        elif data == 'admin_stats':
            await show_stats(update, context)
    
    # Membership check callback
    elif data == "check_membership":
        await check_user_membership(update, context)

async def music_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show music download menu."""
    keyboard = [
        [
            InlineKeyboardButton("Spotify", callback_data="music_spotify"),
            InlineKeyboardButton("Apple Music", callback_data="music_apple")
        ],
        [
            InlineKeyboardButton("SoundCloud", callback_data="music_soundcloud")
        ],
        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="menu_main")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        "لطفاً پلتفرم موسیقی مورد نظر را انتخاب کنید یا مستقیماً لینک آهنگ را ارسال کنید:",
        reply_markup=reply_markup
    )

async def youtube_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show YouTube download menu."""
    keyboard = [
        [
            InlineKeyboardButton("🎬 دانلود ویدیو", callback_data="youtube_video"),
            InlineKeyboardButton("🎵 دانلود صدا", callback_data="youtube_audio")
        ],
        [
            InlineKeyboardButton("📋 دانلود پلی‌لیست", callback_data="youtube_playlist")
        ],
        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="menu_main")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        "لطفاً نوع دانلود از یوتیوب را انتخاب کنید یا مستقیماً لینک ویدیو را ارسال کنید:",
        reply_markup=reply_markup
    )

async def instagram_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show Instagram download menu."""
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
    
    await update.callback_query.edit_message_text(
        "لطفاً نوع دانلود از اینستاگرام را انتخاب کنید یا مستقیماً لینک محتوا را ارسال کنید:",
        reply_markup=reply_markup
    )

async def instagram_type_selected(update: Update, context: ContextTypes.DEFAULT_TYPE, content_type: str) -> None:
    """Handle Instagram content type selection."""
    type_names = {
        'post': 'پست',
        'reel': 'ریلز',
        'story': 'استوری',
        'profile': 'پروفایل'
    }
    
    type_name = type_names.get(content_type, content_type)
    
    keyboard = [[InlineKeyboardButton("🔙 بازگشت", callback_data="menu_instagram")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        f"لطفاً لینک {type_name} اینستاگرام را ارسال کنید:",
        reply_markup=reply_markup
    )

async def playlists_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show playlists menu."""
    user_id = update.effective_user.id
    playlist_model = context.bot_data.get('playlist_model')
    
    # Get user's playlists
    playlists = playlist_model.get_user_playlists(user_id) if playlist_model else []
    
    keyboard = []
    
    # Add playlist buttons
    for playlist in playlists:
        keyboard.append([InlineKeyboardButton(
            f"🎵 {playlist['name']} ({playlist['song_count']} آهنگ)", 
            callback_data=f"playlist_view_{playlist['id']}"
        )])
    
    # Add create playlist button
    keyboard.append([InlineKeyboardButton("➕ ساخت پلی‌لیست جدید", callback_data="playlist_create")])
    
    # Add back button
    keyboard.append([InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="menu_main")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        "پلی‌لیست‌های شما:\n\n"
        "برای ساخت پلی‌لیست جدید، از دکمه زیر یا دستور /create_playlist استفاده کنید.\n"
        "برای مشاهده پلی‌لیست، روی آن کلیک کنید.",
        reply_markup=reply_markup
    )

async def view_playlist(update: Update, context: ContextTypes.DEFAULT_TYPE, playlist_id: str) -> None:
    """Show playlist contents."""
    user_id = update.effective_user.id
    playlist_model = context.bot_data.get('playlist_model')
    song_model = context.bot_data.get('song_model')
    
    # Get playlist info
    playlist = playlist_model.get_playlist(playlist_id) if playlist_model else None
    
    if not playlist or playlist['user_id'] != user_id:
        await update.callback_query.edit_message_text(
            "پلی‌لیست مورد نظر یافت نشد یا شما دسترسی به آن ندارید.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="menu_playlists")]])
        )
        return
    
    # Get songs in playlist
    songs = song_model.get_playlist_songs(playlist_id) if song_model else []
    
    # Create message text
    message_text = f"🎵 پلی‌لیست: {playlist['name']}\n\n"
    
    if songs:
        for i, song in enumerate(songs, 1):
            message_text += f"{i}. {song['title']} - {song['artist']}\n"
    else:
        message_text += "این پلی‌لیست خالی است. برای افزودن آهنگ، هنگام دانلود موزیک، گزینه «افزودن به پلی‌لیست» را انتخاب کنید."
    
    keyboard = [[InlineKeyboardButton("🔙 بازگشت به پلی‌لیست‌ها", callback_data="menu_playlists")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        message_text,
        reply_markup=reply_markup
    )

async def vip_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show VIP subscription menu."""
    user_id = update.effective_user.id
    vip_model = context.bot_data.get('vip_model')
    
    # Check if user is already VIP
    is_vip = vip_model.is_vip(user_id) if vip_model else False
    
    if is_vip:
        # Get VIP info
        vip_info = vip_model.get_vip_info(user_id) if vip_model else None
        
        if vip_info:
            message_text = (
                "⭐️ شما کاربر VIP هستید! ⭐️\n\n"
                f"تاریخ شروع: {vip_info['start_date']}\n"
                f"تاریخ پایان: {vip_info['end_date']}\n\n"
                "مزایای اشتراک VIP:\n"
                "• دانلود نامحدود (بدون محدودیت حجم روزانه)\n"
                "• دسترسی به تمام قابلیت‌های ربات\n"
                "• اولویت در پشتیبانی\n\n"
                "از حمایت شما متشکریم! 🙏"
            )
            
            keyboard = [[InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="menu_main")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.callback_query.edit_message_text(
                message_text,
                reply_markup=reply_markup
            )
        else:
            # Fallback if VIP info not found
            await show_vip_plans(update, context)
    else:
        # Show VIP plans
        await show_vip_plans(update, context)

async def show_vip_plans(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show VIP subscription plans."""
    message_text = (
        "⭐️ اشتراک VIP ⭐️\n\n"
        "با خرید اشتراک VIP از مزایای زیر بهره‌مند شوید:\n"
        "• دانلود نامحدود (بدون محدودیت حجم روزانه)\n"
        "• دسترسی به تمام قابلیت‌های ربات\n"
        "• اولویت در پشتیبانی\n\n"
        "📋 پلن‌های اشتراک:"
    )
    
    keyboard = [
        [
            InlineKeyboardButton("یک ماهه - 50,000 تومان", callback_data="vip_1month")
        ],
        [
            InlineKeyboardButton("سه ماهه - 120,000 تومان", callback_data="vip_3month")
        ],
        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="menu_main")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        message_text,
        reply_markup=reply_markup
    )

async def help_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show help menu."""
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
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        help_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def admin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show admin menu."""
    user_id = update.effective_user.id
    user_model = context.bot_data.get('user_model')
    
    # Check if user is admin
    is_admin = user_model.is_admin(user_id) if user_model else False
    
    if not is_admin:
        await update.callback_query.edit_message_text(
            "شما دسترسی به پنل مدیریت ندارید.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 بازگشت", callback_data="menu_main")]])
        )
        return
    
    keyboard = [
        [
            InlineKeyboardButton("📊 آمار ربات", callback_data="admin_stats"),
            InlineKeyboardButton("📣 ارسال پیام همگانی", callback_data="admin_broadcast")
        ],
        [
            InlineKeyboardButton("📱 مدیریت کانال‌های اجباری", callback_data="admin_channels")
        ],
        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="menu_main")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        "🔐 پنل مدیریت\n\n"
        "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=reply_markup
    )

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show bot statistics."""
    user_model = context.bot_data.get('user_model')
    download_model = context.bot_data.get('download_model')
    vip_model = context.bot_data.get('vip_model')
    
    # Get statistics
    total_users = user_model.get_total_users() if user_model else 0
    active_users = user_model.get_active_users_count() if user_model else 0
    total_downloads = download_model.get_total_downloads() if download_model else 0
    total_vip_users = vip_model.get_total_vip_users() if vip_model else 0
    
    message_text = (
        "📊 آمار ربات\n\n"
        f"👥 کاربران: {total_users}\n"
        f"👤 کاربران فعال: {active_users}\n"
        f"⭐️ کاربران VIP: {total_vip_users}\n"
        f"📥 تعداد دانلودها: {total_downloads}\n"
    )
    
    keyboard = [[InlineKeyboardButton("🔙 بازگشت به پنل مدیریت", callback_data="menu_admin")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.callback_query.edit_message_text(
        message_text,
        reply_markup=reply_markup
    )

async def check_user_membership(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check if user has joined required channels."""
    user = update.effective_user
    channel_model = context.bot_data.get('channel_model')
    
    # Get required channels
    required_channels = channel_model.get_all_channels() if channel_model else []
    
    if not required_channels:
        # No required channels, show main menu
        await callback_handler(update, context)
        return
    
    # Check if user is member of all required channels
    all_joined = True
    channels_keyboard = []
    
    for channel in required_channels:
        try:
            member = await context.bot.get_chat_member(chat_id=channel['channel_id'], user_id=user.id)
            if member.status in ['left', 'kicked', 'restricted']:
                all_joined = False
                channels_keyboard.append([
                    InlineKeyboardButton(text=f"عضویت در {channel['channel_name']}", url=channel['channel_url'])
                ])
        except Exception as e:
            # Bot might not be admin in the channel or channel might not exist
            logger.error(f"Error checking membership: {e}")
            continue
    
    if not all_joined:
        channels_keyboard.append([InlineKeyboardButton(text="بررسی مجدد عضویت", callback_data="check_membership")])
        reply_markup = InlineKeyboardMarkup(channels_keyboard)
        
        await update.callback_query.edit_message_text(
            "برای استفاده از ربات، لطفا در کانال‌های زیر عضو شوید:",
            reply_markup=reply_markup
        )
    else:
        # User has joined all channels, show main menu
        await callback_handler(update, context)

if __name__ == '__main__':
    main()
