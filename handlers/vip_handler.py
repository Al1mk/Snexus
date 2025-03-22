from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import datetime
from models.models import User, VIPSubscription
from config.config import ONE_MONTH_PRICE, THREE_MONTH_PRICE, PAYMENT_CARD_NUMBER, PAYMENT_CARD_OWNER
from services.vip_service import VIPService
import logging

logger = logging.getLogger(__name__)

async def vip_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /vip command."""
    user_id = update.effective_user.id
    
    # Initialize database models
    db = context.bot_data.get('db')
    vip_service = VIPService(db)
    
    # Check if user has active subscription
    subscription = vip_service.get_subscription(user_id)
    
    if subscription:
        # User has active subscription
        end_date = subscription['end_date'].strftime('%Y-%m-%d')
        
        keyboard = [
            [InlineKeyboardButton("تمدید اشتراک", callback_data="menu_vip_extend")],
            [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="menu_main")]
        ]
        
        await update.message.reply_text(
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
        keyboard = [
            [
                InlineKeyboardButton(f"یک ماهه ({ONE_MONTH_PRICE} تومان)", callback_data="vip_1month"),
                InlineKeyboardButton(f"سه ماهه ({THREE_MONTH_PRICE} تومان)", callback_data="vip_3month")
            ],
            [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="menu_main")]
        ]
        
        await update.message.reply_text(
            "⭐️ *اشتراک VIP*\n\n"
            "با خرید اشتراک VIP می‌توانید:\n"
            "• بدون محدودیت دانلود کنید (بدون سقف ۲ گیگابایت روزانه)\n"
            "• به تمام قابلیت‌های ربات دسترسی داشته باشید\n"
            "• پلی‌لیست‌های نامحدود بسازید\n\n"
            "لطفاً نوع اشتراک مورد نظر خود را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )

async def process_vip_payment(update: Update, context: ContextTypes.DEFAULT_TYPE, subscription_type: str) -> None:
    """Process VIP subscription payment."""
    query = update.callback_query
    user_id = update.effective_user.id
    
    # Initialize database models
    db = context.bot_data.get('db')
    vip_service = VIPService(db)
    
    # Determine subscription details
    if subscription_type == "one_month":
        price = ONE_MONTH_PRICE
        duration = "یک ماهه"
        subscription_days = 30
    elif subscription_type == "three_month":
        price = THREE_MONTH_PRICE
        duration = "سه ماهه"
        subscription_days = 90
    else:
        await query.answer("❌ نوع اشتراک نامعتبر است.")
        return
    
    # Check if card info is available
    if not PAYMENT_CARD_NUMBER or not PAYMENT_CARD_OWNER:
        await query.message.edit_text(
            "⚠️ اطلاعات پرداخت در دسترس نیست. لطفاً با پشتیبانی تماس بگیرید."
        )
        return
    
    # Calculate subscription dates
    start_date = datetime.datetime.now()
    end_date = start_date + datetime.timedelta(days=subscription_days)
    
    # Send payment information
    keyboard = [
        [InlineKeyboardButton("✅ پرداخت انجام شد", callback_data=f"payment_done_{subscription_type}_{price}")],
        [InlineKeyboardButton("❌ انصراف", callback_data="menu_vip")]
    ]
    
    await query.message.edit_text(
        f"💳 *اطلاعات پرداخت اشتراک {duration}*\n\n"
        f"مبلغ: {price} تومان\n"
        f"شماره کارت: `{PAYMENT_CARD_NUMBER}`\n"
        f"به نام: {PAYMENT_CARD_OWNER}\n\n"
        f"تاریخ شروع اشتراک: {start_date.strftime('%Y-%m-%d')}\n"
        f"تاریخ پایان اشتراک: {end_date.strftime('%Y-%m-%d')}\n\n"
        "پس از واریز مبلغ، روی دکمه «پرداخت انجام شد» کلیک کنید.\n"
        "توجه: اطلاعات پرداخت خود را برای پیگیری‌های بعدی نگهداری کنید.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def handle_payment_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE, callback_data: str) -> None:
    """Handle payment confirmation."""
    query = update.callback_query
    user_id = update.effective_user.id
    
    # Parse callback data
    parts = callback_data.split("_")
    subscription_type = parts[2]
    payment_amount = int(parts[3])
    
    # Initialize database models
    db = context.bot_data.get('db')
    vip_service = VIPService(db)
    user_model = User(db)
    
    # Check if user exists
    user_data = user_model.get_user(user_id)
    if not user_data:
        user_model.create_user(
            user_id=user_id,
            username=update.effective_user.username,
            first_name=update.effective_user.first_name,
            last_name=update.effective_user.last_name
        )
    
    # Generate payment reference
    payment_ref = f"VIP_{user_id}_{int(datetime.datetime.now().timestamp())}"
    
    # Create subscription
    subscription = vip_service.create_subscription(
        user_id=user_id,
        subscription_type=subscription_type,
        payment_amount=payment_amount,
        payment_method="card",
        payment_ref=payment_ref
    )
    
    if subscription:
        # Update user's VIP status
        user_model.update_user(user_id, {'is_vip': True})
        
        keyboard = [
            [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="menu_main")]
        ]
        
        await query.message.edit_text(
            "✅ *اشتراک VIP شما با موفقیت فعال شد*\n\n"
            f"نوع اشتراک: {'یک ماهه' if subscription_type == 'one_month' else 'سه ماهه'}\n"
            f"تاریخ شروع: {subscription['start_date'].strftime('%Y-%m-%d')}\n"
            f"تاریخ پایان: {subscription['end_date'].strftime('%Y-%m-%d')}\n"
            f"شماره پیگیری: `{payment_ref}`\n\n"
            "اکنون می‌توانید از تمامی امکانات VIP استفاده کنید:\n"
            "• دانلود نامحدود\n"
            "• ساخت پلی‌لیست‌های نامحدود\n"
            "• دسترسی به تمام قابلیت‌های ربات\n\n"
            "با تشکر از اعتماد شما",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    else:
        await query.message.edit_text(
            "❌ خطا در فعال‌سازی اشتراک VIP. لطفاً مجدداً تلاش کنید یا با پشتیبانی تماس بگیرید."
        )

async def handle_vip_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, callback_data: str) -> None:
    """Handle VIP-related callback queries."""
    query = update.callback_query
    
    if callback_data == "menu_vip_extend":
        # Show subscription extension options
        keyboard = [
            [
                InlineKeyboardButton(f"یک ماهه ({ONE_MONTH_PRICE} تومان)", callback_data="vip_extend_1month"),
                InlineKeyboardButton(f"سه ماهه ({THREE_MONTH_PRICE} تومان)", callback_data="vip_extend_3month")
            ],
            [InlineKeyboardButton("🔙 بازگشت", callback_data="menu_vip")]
        ]
        
        await query.message.edit_text(
            "⭐️ *تمدید اشتراک VIP*\n\n"
            "لطفاً مدت زمان تمدید اشتراک خود را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    elif callback_data.startswith("vip_extend_"):
        # Handle subscription extension
        subscription_type = callback_data.split("_")[-1]
        if subscription_type == "1month":
            await process_vip_payment(update, context, "one_month")
        elif subscription_type == "3month":
            await process_vip_payment(update, context, "three_month")
    
    elif callback_data.startswith("payment_done_"):
        # Handle payment confirmation
        await handle_payment_confirmation(update, context, callback_data)
