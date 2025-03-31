from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import logging
from models.models import User, RequiredChannel
from config.config import ADMIN_USER_IDS as ADMIN_IDS
from services.admin_service import AdminService

logger = logging.getLogger(__name__)

async def admin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /admin command."""
    user_id = update.effective_user.id
    
    # Check if user is admin
    if user_id not in ADMIN_IDS:
        await update.message.reply_text(
            "⛔️ شما دسترسی به پنل مدیریت را ندارید."
        )
        return
    
    # Initialize database models
    db = context.bot_data.get('db')
    admin_service = AdminService(db)
    
    # Get user stats
    user_stats = admin_service.get_user_stats()
    
    # Get required channels
    required_channels = admin_service.get_required_channels()
    
    keyboard = [
        [
            InlineKeyboardButton("📊 آمار کاربران", callback_data="admin_stats"),
            InlineKeyboardButton("📢 ارسال پیام همگانی", callback_data="admin_broadcast")
        ],
        [
            InlineKeyboardButton("📤 فوروارد پیام همگانی", callback_data="admin_forward"),
            InlineKeyboardButton("📋 مدیریت کانال‌های اجباری", callback_data="admin_channels")
        ],
        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="menu_main")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🔐 *پنل مدیریت*\n\n"
        f"👥 تعداد کل کاربران: {user_stats['total_users']}\n"
        f"👤 کاربران فعال (7 روز اخیر): {user_stats['active_users']}\n"
        f"⭐️ کاربران VIP: {user_stats['vip_users']}\n\n"
        f"📢 کانال‌های اجباری: {len(required_channels)}\n\n"
        "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def handle_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, callback_data: str) -> None:
    """Handle admin-related callback queries."""
    query = update.callback_query
    user_id = update.effective_user.id
    
    # Check if user is admin
    if user_id not in ADMIN_IDS:
        await query.answer("⛔️ شما دسترسی به پنل مدیریت را ندارید.")
        return
    
    # Initialize database models
    db = context.bot_data.get('db')
    admin_service = AdminService(db)
    
    if callback_data == "admin_stats":
        # Show detailed user statistics
        user_stats = admin_service.get_user_stats()
        active_users = admin_service.get_active_users(7)
        vip_users = admin_service.get_vip_users()
        
        keyboard = [
            [InlineKeyboardButton("🔙 بازگشت به پنل مدیریت", callback_data="menu_admin")]
        ]
        
        await query.message.edit_text(
            "📊 *آمار کاربران*\n\n"
            f"👥 تعداد کل کاربران: {user_stats['total_users']}\n"
            f"👤 کاربران فعال (7 روز اخیر): {user_stats['active_users']}\n"
            f"⭐️ کاربران VIP: {user_stats['vip_users']}\n\n"
            "📈 *آمار دقیق*\n"
            f"• کاربران فعال امروز: {len([u for u in active_users if u.get('last_activity_days', 0) < 1])}\n"
            f"• کاربران فعال هفته اخیر: {len(active_users)}\n"
            f"• کاربران VIP فعال: {len([u for u in vip_users if u.get('last_activity_days', 0) < 7])}\n",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    elif callback_data == "admin_broadcast":
        # Show broadcast message form
        context.user_data['admin_action'] = 'broadcast'
        
        keyboard = [
            [InlineKeyboardButton("🔙 بازگشت به پنل مدیریت", callback_data="menu_admin")]
        ]
        
        await query.message.edit_text(
            "📢 *ارسال پیام همگانی*\n\n"
            "لطفاً متن پیام خود را ارسال کنید.\n"
            "این پیام برای تمام کاربران ربات ارسال خواهد شد.\n\n"
            "توجه: برای لغو عملیات، از دکمه بازگشت استفاده کنید.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    elif callback_data == "admin_forward":
        # Show forward message form
        context.user_data['admin_action'] = 'forward'
        
        keyboard = [
            [InlineKeyboardButton("🔙 بازگشت به پنل مدیریت", callback_data="menu_admin")]
        ]
        
        await query.message.edit_text(
            "📤 *فوروارد پیام همگانی*\n\n"
            "لطفاً پیامی که می‌خواهید فوروارد شود را به ربات فوروارد کنید.\n"
            "این پیام برای تمام کاربران ربات فوروارد خواهد شد.\n\n"
            "توجه: برای لغو عملیات، از دکمه بازگشت استفاده کنید.",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    elif callback_data == "admin_channels":
        # Show required channels management
        required_channels = admin_service.get_required_channels()
        
        message = "📋 *مدیریت کانال‌های اجباری*\n\n"
        
        if required_channels:
            message += "کانال‌های فعلی:\n"
            for i, channel in enumerate(required_channels, 1):
                message += f"{i}. {channel['channel_name']} - {channel['channel_url']}\n"
        else:
            message += "هیچ کانالی تنظیم نشده است.\n"
        
        message += "\nحداکثر 5 کانال می‌توانید تنظیم کنید."
        
        keyboard = [
            [InlineKeyboardButton("➕ افزودن کانال", callback_data="admin_add_channel")]
        ]
        
        # Add remove buttons for each channel
        for channel in required_channels:
            keyboard.append([
                InlineKeyboardButton(
                    f"❌ حذف {channel['channel_name']}", 
                    callback_data=f"admin_remove_channel_{channel['channel_id']}"
                )
            ])
        
        keyboard.append([InlineKeyboardButton("🔙 بازگشت به پنل مدیریت", callback_data="menu_admin")])
        
        await query.message.edit_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    elif callback_data == "admin_add_channel":
        # Show add channel form
        if len(admin_service.get_required_channels()) >= 5:
            await query.answer("⚠️ حداکثر تعداد کانال‌های مجاز (5) تنظیم شده است.")
            return
        
        context.user_data['admin_action'] = 'add_channel'
        
        keyboard = [
            [InlineKeyboardButton("🔙 بازگشت به مدیریت کانال‌ها", callback_data="admin_channels")]
        ]
        
        await query.message.edit_text(
            "➕ *افزودن کانال اجباری*\n\n"
            "لطفاً اطلاعات کانال را در قالب زیر ارسال کنید:\n\n"
            "`@username | نام کانال`\n\n"
            "مثال:\n"
            "`@snexus_channel | کانال رسمی Snexus`\n\n"
            "توجه:\n"
            "• ربات باید در کانال ادمین باشد\n"
            "• کانال باید عمومی باشد\n"
            "• حداکثر 5 کانال می‌توانید تنظیم کنید",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    elif callback_data.startswith("admin_remove_channel_"):
        # Remove channel
        channel_id = callback_data.split("_")[-1]
        
        result = admin_service.remove_required_channel(channel_id)
        
        if result:
            await query.answer("✅ کانال با موفقیت حذف شد.")
        else:
            await query.answer("❌ خطا در حذف کانال.")
        
        # Refresh channels list
        await handle_admin_callback(update, context, "admin_channels")

async def process_admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Process admin message based on current action."""
    user_id = update.effective_user.id
    
    # Check if user is admin
    if user_id not in ADMIN_IDS:
        return
    
    # Check if admin action is set
    if 'admin_action' not in context.user_data:
        return
    
    admin_action = context.user_data['admin_action']
    
    # Initialize database models
    db = context.bot_data.get('db')
    admin_service = AdminService(db)
    
    if admin_action == 'broadcast':
        # Process broadcast message
        message_text = update.message.text
        
        # Send confirmation
        keyboard = [
            [
                InlineKeyboardButton("✅ بله، ارسال شود", callback_data="admin_confirm_broadcast"),
                InlineKeyboardButton("❌ خیر، لغو شود", callback_data="menu_admin")
            ]
        ]
        
        # Store message in context
        context.user_data['broadcast_message'] = message_text
        
        await update.message.reply_text(
            "📢 *تأیید ارسال پیام همگانی*\n\n"
            "آیا از ارسال پیام زیر به تمام کاربران اطمینان دارید؟\n\n"
            f"```\n{message_text}\n```",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    elif admin_action == 'forward':
        # Process forward message
        if update.message.forward_date:
            # Store message info in context
            context.user_data['forward_from_chat_id'] = update.message.forward_from_chat.id
            context.user_data['forward_message_id'] = update.message.message_id
            
            # Send confirmation
            keyboard = [
                [
                    InlineKeyboardButton("✅ بله، فوروارد شود", callback_data="admin_confirm_forward"),
                    InlineKeyboardButton("❌ خیر، لغو شود", callback_data="menu_admin")
                ]
            ]
            
            await update.message.reply_text(
                "📤 *تأیید فوروارد پیام همگانی*\n\n"
                "آیا از فوروارد پیام بالا به تمام کاربران اطمینان دارید؟",
                reply_markup=InlineKeyboardMarkup(keyboard),
                parse_mode='Markdown'
            )
        else:
            await update.message.reply_text(
                "❌ لطفاً یک پیام فوروارد شده ارسال کنید."
            )
    
    elif admin_action == 'add_channel':
        # Process add channel
        text = update.message.text
        
        # Parse channel info
        try:
            parts = text.split('|')
            channel_username = parts[0].strip()
            channel_name = parts[1].strip() if len(parts) > 1 else channel_username
            
            # Validate username
            if not channel_username.startswith('@'):
                await update.message.reply_text(
                    "❌ نام کاربری کانال باید با @ شروع شود."
                )
                return
            
            # Add channel
            channel_id = channel_username.replace('@', '')
            channel_url = f"https://t.me/{channel_id}"
            
            result = admin_service.add_required_channel(channel_id, channel_name, channel_url)
            
            if result:
                # Clear admin action
                context.user_data.pop('admin_action', None)
                
                keyboard = [
                    [InlineKeyboardButton("🔙 بازگشت به مدیریت کانال‌ها", callback_data="admin_channels")]
                ]
                
                await update.message.reply_text(
                    f"✅ کانال «{channel_name}» با موفقیت اضافه شد.",
                    reply_markup=InlineKeyboardMarkup(keyboard)
                )
            else:
                await update.message.reply_text(
                    "❌ خطا در افزودن کانال. لطفاً مجدداً تلاش کنید."
                )
        except Exception as e:
            logger.error(f"Error adding channel: {e}")
            await update.message.reply_text(
                "❌ فرمت وارد شده نامعتبر است. لطفاً از فرمت `@username | نام کانال` استفاده کنید."
            )

async def handle_admin_confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, callback_data: str) -> None:
    """Handle admin confirmation callback queries."""
    query = update.callback_query
    user_id = update.effective_user.id
    
    # Check if user is admin
    if user_id not in ADMIN_IDS:
        await query.answer("⛔️ شما دسترسی به پنل مدیریت را ندارید.")
        return
    
    # Initialize database models
    db = context.bot_data.get('db')
    admin_service = AdminService(db)
    
    if callback_data == "admin_confirm_broadcast":
        # Confirm broadcast message
        if 'broadcast_message' not in context.user_data:
            await query.answer("❌ پیامی برای ارسال یافت نشد.")
            return
        
        message_text = context.user_data['broadcast_message']
        
        # Send processing message
        await query.message.edit_text(
            "📢 در حال ارسال پیام همگانی...\n"
            "این عملیات ممکن است چند دقیقه طول بکشد."
        )
        
        # Broadcast message
        result = await admin_service.broadcast_message(context.bot, message_text)
        
        # Clear user data
        context.user_data.pop('admin_action', None)
        context.user_data.pop('broadcast_message', None)
        
        if result:
            keyboard = [
                [InlineKeyboardButton("🔙 بازگشت به پنل مدیریت", callback_data="menu_admin")]
            ]
            
            await query.message.edit_text(
                f"✅ پیام همگانی با موفقیت ارسال شد.\n\n"
                f"📊 آمار ارسال:\n"
                f"• تعداد کل: {result['total']}\n"
                f"• موفق: {result['success']}\n"
                f"• ناموفق: {result['fail']}",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await query.message.edit_text(
                "❌ خطا در ارسال پیام همگانی."
            )
    
    elif callback_data == "admin_confirm_forward":
        # Confirm forward message
        if 'forward_from_chat_id' not in context.user_data or 'forward_message_id' not in context.user_data:
            await query.answer("❌ پیامی برای فوروارد یافت نشد.")
            return
        
        from_chat_id = context.user_data['forward_from_chat_id']
        message_id = context.user_data['forward_message_id']
        
        # Send processing message
        await query.message.edit_text(
            "📤 در حال فوروارد پیام همگانی...\n"
            "این عملیات ممکن است چند دقیقه طول بکشد."
        )
        
        # Forward message
        result = await admin_service.forward_message(context.bot, from_chat_id, message_id)
        
        # Clear user data
        context.user_data.pop('admin_action', None)
        context.user_data.pop('forward_from_chat_id', None)
        context.user_data.pop('forward_message_id', None)
        
        if result:
            keyboard = [
                [InlineKeyboardButton("🔙 بازگشت به پنل مدیریت", callback_data="menu_admin")]
            ]
            
            await query.message.edit_text(
                f"✅ پیام همگانی با موفقیت فوروارد شد.\n\n"
                f"📊 آمار ارسال:\n"
                f"• تعداد کل: {result['total']}\n"
                f"• موفق: {result['success']}\n"
                f"• ناموفق: {result['fail']}",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await query.message.edit_text(
                "❌ خطا در فوروارد پیام همگانی."
            )
