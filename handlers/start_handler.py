from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from models.models import User, RequiredChannel
from config.config import ADMIN_USER_IDS

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /start command."""
    user = update.effective_user
    
    # Initialize database models
    db = context.bot_data.get('db')
    user_model = User(db)
    channel_model = RequiredChannel(db)
    
    # Create or update user in database
    user_model.create_user(
        user_id=user.id,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        is_admin=user.id in ADMIN_USER_IDS
    )
    
    # Check if user needs to join required channels
    required_channels = channel_model.get_all_channels()
    if required_channels:
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
                continue
        
        if not all_joined:
            channels_keyboard.append([InlineKeyboardButton(text="بررسی مجدد عضویت", callback_data="check_membership")])
            reply_markup = InlineKeyboardMarkup(channels_keyboard)
            
            await update.message.reply_text(
                "برای استفاده از ربات، لطفا در کانال‌های زیر عضو شوید:",
                reply_markup=reply_markup
            )
            return
    
    # Main menu keyboard
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
    if user_model.is_admin(user.id):
        keyboard.append([InlineKeyboardButton("🔐 پنل مدیریت", callback_data="menu_admin")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"سلام {user.first_name}! به ربات Snexus خوش آمدید.\n\n"
        "با این ربات می‌توانید:\n"
        "• موزیک از پلتفرم‌های مختلف دانلود کنید\n"
        "• ویدیو از یوتیوب دانلود کنید\n"
        "• محتوا از اینستاگرام دانلود کنید\n"
        "• پلی‌لیست‌های شخصی بسازید\n\n"
        "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=reply_markup
    )

async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /help command."""
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
    
    await update.message.reply_text(
        help_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
