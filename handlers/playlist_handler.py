from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import os
from models.models import User, VIPSubscription, Song, Playlist
from utils.helpers import create_download_dir, format_size
from config.config import DOWNLOAD_DIR
from services.playlist_service import PlaylistService
import logging

logger = logging.getLogger(__name__)

async def playlist_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /playlist command."""
    user_id = update.effective_user.id
    
    # Initialize database models
    db = context.bot_data.get('db')
    playlist_service = PlaylistService(db)
    
    # Get user's playlists
    playlists = playlist_service.get_user_playlists(user_id)
    
    keyboard = [
        [InlineKeyboardButton("➕ ایجاد پلی‌لیست جدید", callback_data="playlist_create")],
    ]
    
    # Add user's playlists to keyboard
    if playlists:
        for playlist in playlists:
            keyboard.append([
                InlineKeyboardButton(
                    f"🎵 {playlist['name']} ({playlist['songs_count']} آهنگ)", 
                    callback_data=f"playlist_view_{playlist['id']}"
                )
            ])
    
    keyboard.append([InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="menu_main")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🎵 *مدیریت پلی‌لیست‌ها*\n\n"
        "در این بخش می‌توانید پلی‌لیست‌های خود را مدیریت کنید، "
        "آهنگ‌های مورد علاقه خود را به آن‌ها اضافه کنید و آن‌ها را با دوستان خود به اشتراک بگذارید.\n\n"
        "لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def create_playlist_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /create_playlist command."""
    # Check if command has arguments
    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            "❌ لطفاً نام پلی‌لیست را وارد کنید.\n"
            "مثال: /create_playlist نام پلی‌لیست"
        )
        return
    
    user_id = update.effective_user.id
    playlist_name = ' '.join(context.args)
    
    # Initialize database models
    db = context.bot_data.get('db')
    playlist_service = PlaylistService(db)
    vip_model = VIPSubscription(db)
    
    # Check if user is VIP for creating multiple playlists
    is_vip = vip_model.is_vip(user_id)
    
    if not is_vip:
        # Check how many playlists user already has
        playlists = playlist_service.get_user_playlists(user_id)
        if len(playlists) >= 3:  # Non-VIP users can have up to 3 playlists
            vip_keyboard = [
                [InlineKeyboardButton("خرید اشتراک VIP", callback_data="menu_vip")],
                [InlineKeyboardButton("🔙 بازگشت به منوی پلی‌لیست‌ها", callback_data="menu_playlists")]
            ]
            await update.message.reply_text(
                "⚠️ شما به محدودیت تعداد پلی‌لیست‌ها رسیده‌اید.\n"
                "کاربران عادی می‌توانند حداکثر 3 پلی‌لیست ایجاد کنند.\n"
                "برای ایجاد پلی‌لیست‌های نامحدود، اشتراک VIP تهیه کنید.",
                reply_markup=InlineKeyboardMarkup(vip_keyboard)
            )
            return
    
    # Create playlist
    result = playlist_service.create_playlist(user_id, playlist_name)
    
    if result:
        keyboard = [
            [InlineKeyboardButton("مشاهده پلی‌لیست‌ها", callback_data="menu_playlists")],
            [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="menu_main")]
        ]
        
        await update.message.reply_text(
            f"✅ پلی‌لیست «{playlist_name}» با موفقیت ایجاد شد.\n\n"
            "برای افزودن آهنگ به این پلی‌لیست، هنگام دانلود آهنگ از گزینه «افزودن به پلی‌لیست» استفاده کنید.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.message.reply_text(
            "❌ خطا در ایجاد پلی‌لیست. لطفاً مجدداً تلاش کنید."
        )

async def view_playlists_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /my_playlists command."""
    user_id = update.effective_user.id
    
    # Initialize database models
    db = context.bot_data.get('db')
    playlist_service = PlaylistService(db)
    
    # Get user's playlists
    playlists = playlist_service.get_user_playlists(user_id)
    
    if not playlists:
        keyboard = [
            [InlineKeyboardButton("➕ ایجاد پلی‌لیست جدید", callback_data="playlist_create")],
            [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="menu_main")]
        ]
        
        await update.message.reply_text(
            "❌ شما هنوز هیچ پلی‌لیستی ندارید.\n"
            "برای ایجاد پلی‌لیست جدید، از دکمه زیر استفاده کنید:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return
    
    # Create message with playlists
    message = "🎵 *پلی‌لیست‌های شما*\n\n"
    
    for i, playlist in enumerate(playlists, 1):
        message += f"{i}. *{playlist['name']}* - {playlist['songs_count']} آهنگ\n"
        if playlist['description']:
            message += f"   {playlist['description']}\n"
    
    keyboard = [
        [InlineKeyboardButton("➕ ایجاد پلی‌لیست جدید", callback_data="playlist_create")],
        [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="menu_main")]
    ]
    
    await update.message.reply_text(
        message,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def handle_playlist_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, callback_data: str) -> None:
    """Handle playlist-related callback queries."""
    query = update.callback_query
    user_id = update.effective_user.id
    
    # Initialize database models
    db = context.bot_data.get('db')
    playlist_service = PlaylistService(db)
    
    if callback_data == "playlist_create":
        # Show playlist creation form
        await query.message.edit_text(
            "🎵 *ایجاد پلی‌لیست جدید*\n\n"
            "برای ایجاد پلی‌لیست جدید، از دستور زیر استفاده کنید:\n"
            "/create_playlist نام پلی‌لیست\n\n"
            "مثال: /create_playlist آهنگ‌های مورد علاقه",
            parse_mode='Markdown'
        )
    
    elif callback_data.startswith("playlist_view_"):
        # View playlist details
        playlist_id = int(callback_data.split("_")[-1])
        playlist = playlist_service.get_playlist(playlist_id)
        
        if not playlist:
            await query.answer("❌ پلی‌لیست یافت نشد.")
            return
        
        # Check if playlist belongs to user
        if playlist['user_id'] != user_id:
            await query.answer("❌ شما به این پلی‌لیست دسترسی ندارید.")
            return
        
        # Create message with playlist details
        message = f"🎵 *پلی‌لیست: {playlist['name']}*\n\n"
        
        if playlist['description']:
            message += f"{playlist['description']}\n\n"
        
        message += f"🔢 تعداد آهنگ‌ها: {playlist['songs_count']}\n\n"
        
        # Add songs
        if playlist['songs']:
            message += "📋 *لیست آهنگ‌ها:*\n"
            for i, song in enumerate(playlist['songs'], 1):
                message += f"{i}. {song['title']} - {song['artist']}\n"
        else:
            message += "❌ این پلی‌لیست خالی است. برای افزودن آهنگ، هنگام دانلود آهنگ از گزینه «افزودن به پلی‌لیست» استفاده کنید."
        
        # Create keyboard
        keyboard = []
        
        if playlist['songs']:
            keyboard.append([
                InlineKeyboardButton("🔄 دریافت کل پلی‌لیست", callback_data=f"playlist_download_{playlist_id}"),
                InlineKeyboardButton("📤 اشتراک‌گذاری", callback_data=f"playlist_share_{playlist_id}")
            ])
        
        keyboard.append([InlineKeyboardButton("❌ حذف پلی‌لیست", callback_data=f"playlist_delete_{playlist_id}")])
        keyboard.append([InlineKeyboardButton("🔙 بازگشت به لیست پلی‌لیست‌ها", callback_data="menu_playlists")])
        
        await query.message.edit_text(
            message,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    elif callback_data.startswith("playlist_download_"):
        # Download all songs in playlist
        playlist_id = int(callback_data.split("_")[-1])
        playlist = playlist_service.get_playlist(playlist_id)
        
        if not playlist or not playlist['songs']:
            await query.answer("❌ پلی‌لیست خالی است یا یافت نشد.")
            return
        
        # Check if playlist belongs to user
        if playlist['user_id'] != user_id:
            await query.answer("❌ شما به این پلی‌لیست دسترسی ندارید.")
            return
        
        # Send message
        await query.message.edit_text(
            f"🎵 در حال ارسال آهنگ‌های پلی‌لیست «{playlist['name']}»...\n"
            f"تعداد آهنگ‌ها: {playlist['songs_count']}"
        )
        
        # Send each song
        for song in playlist['songs']:
            if os.path.exists(song['file_path']):
                with open(song['file_path'], 'rb') as audio_file:
                    await context.bot.send_audio(
                        chat_id=user_id,
                        audio=audio_file,
                        title=song['title'],
                        performer=song['artist'],
                        caption=f"🎵 {song['title']} - {song['artist']}\n\n"
                                f"از پلی‌لیست: {playlist['name']}\n"
                                f"دانلود شده توسط ربات Snexus"
                    )
            else:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"❌ فایل آهنگ «{song['title']}» یافت نشد."
                )
        
        # Final message
        keyboard = [
            [InlineKeyboardButton("🔙 بازگشت به جزئیات پلی‌لیست", callback_data=f"playlist_view_{playlist_id}")],
            [InlineKeyboardButton("🔙 بازگشت به لیست پلی‌لیست‌ها", callback_data="menu_playlists")]
        ]
        
        await query.message.edit_text(
            f"✅ تمام آهنگ‌های پلی‌لیست «{playlist['name']}» ارسال شد.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif callback_data.startswith("playlist_share_"):
        # Share playlist
        playlist_id = int(callback_data.split("_")[-1])
        
        # Get share text
        share_text = playlist_service.get_playlist_share_text(playlist_id)
        
        if not share_text:
            await query.answer("❌ خطا در اشتراک‌گذاری پلی‌لیست.")
            return
        
        # Create file
        user_download_dir = create_download_dir(DOWNLOAD_DIR, user_id)
        file_path = playlist_service.export_playlist_as_file(playlist_id, user_download_dir)
        
        # Send message
        await context.bot.send_message(
            chat_id=user_id,
            text=share_text,
            parse_mode='Markdown'
        )
        
        # Send file if available
        if file_path and os.path.exists(file_path):
            with open(file_path, 'rb') as f:
                await context.bot.send_document(
                    chat_id=user_id,
                    document=f,
                    caption="📋 فایل پلی‌لیست"
                )
        
        # Answer query
        await query.answer("✅ پلی‌لیست با موفقیت اشتراک‌گذاری شد.")
    
    elif callback_data.startswith("playlist_delete_"):
        # Delete playlist
        playlist_id = int(callback_data.split("_")[-1])
        
        # Confirm deletion
        keyboard = [
            [
                InlineKeyboardButton("✅ بله، حذف شود", callback_data=f"playlist_delete_confirm_{playlist_id}"),
                InlineKeyboardButton("❌ خیر", callback_data=f"playlist_view_{playlist_id}")
            ]
        ]
        
        await query.message.edit_text(
            "⚠️ آیا از حذف این پلی‌لیست اطمینان دارید؟\n"
            "این عملیات غیرقابل بازگشت است.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif callback_data.startswith("playlist_delete_confirm_"):
        # Confirm playlist deletion
        playlist_id = int(callback_data.split("_")[-1])
        
        # Delete playlist
        result = playlist_service.delete_playlist(playlist_id, user_id)
        
        if result:
            keyboard = [
                [InlineKeyboardButton("🔙 بازگشت به لیست پلی‌لیست‌ها", callback_data="menu_playlists")]
            ]
            
            await query.message.edit_text(
                "✅ پلی‌لیست با موفقیت حذف شد.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await query.answer("❌ خطا در حذف پلی‌لیست.")
    
    elif callback_data.startswith("add_to_playlist_"):
        # Add song to playlist
        song_id = int(callback_data.split("_")[-1])
        
        # Get user's playlists
        playlists = playlist_service.get_user_playlists(user_id)
        
        if not playlists:
            # No playlists, offer to create one
            keyboard = [
                [InlineKeyboardButton("➕ ایجاد پلی‌لیست جدید", callback_data="playlist_create")],
                [InlineKeyboardButton("🔙 بازگشت", callback_data="menu_main")]
            ]
            
            await query.message.edit_text(
                "❌ شما هنوز هیچ پلی‌لیستی ندارید.\n"
                "برای افزودن آهنگ به پلی‌لیست، ابتدا یک پلی‌لیست ایجاد کنید:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return
        
        # Create keyboard with playlists
        keyboard = []
        for playlist in playlists:
            keyboard.append([
                InlineKeyboardButton(
                    f"🎵 {playlist['name']} ({playlist['songs_count']} آهنگ)", 
                    callback_data=f"add_song_{song_id}_to_playlist_{playlist['id']}"
                )
            ])
        
        keyboard.append([InlineKeyboardButton("🔙 بازگشت", callback_data="menu_main")])
        
        await query.message.edit_text(
            "🎵 *افزودن به پلی‌لیست*\n\n"
            "لطفاً پلی‌لیست مورد نظر خود را انتخاب کنید:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    elif callback_data.startswith("add_song_"):
        # Add song to specific playlist
        parts = callback_data.split("_")
        song_id = int(parts[1])
        playlist_id = int(parts[4])
        
        # Add song to playlist
        result = playlist_service.add_song_to_playlist(playlist_id, song_id)
        
        if result:
            # Get playlist name
            playlist = playlist_service.get_playlist(playlist_id)
            playlist_name = playlist['name'] if playlist else "پلی‌لیست"
            
            keyboard = [
                [InlineKeyboardButton("مشاهده پلی‌لیست", callback_data=f"playlist_view_{playlist_id}")],
                [InlineKeyboardButton("🔙 بازگشت به منوی اصلی", callback_data="menu_main")]
            ]
            
            await query.message.edit_text(
                f"✅ آهنگ با موفقیت به پلی‌لیست «{playlist_name}» اضافه شد.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await query.answer("❌ خطا در افزودن آهنگ به پلی‌لیست.")
