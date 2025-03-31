import logging
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from models.models import User, RequiredChannel
from config.config import ADMIN_USER_IDS as ADMIN_IDS
import time

logger = logging.getLogger(__name__)

class AdminService:
    """Service for admin management features"""
    
    def __init__(self, db):
        self.db = db
        self.required_channel_model = RequiredChannel(db)
        self.user_model = User(db)
    
    def get_required_channels(self):
        """Get all required channels"""
        try:
            return self.required_channel_model.get_all_channels()
        except Exception as e:
            logger.error(f"Error getting required channels: {e}")
            return []
    
    def add_required_channel(self, channel_id, channel_name, channel_url):
        """Add a required channel"""
        try:
            return self.required_channel_model.add_channel(
                channel_id=channel_id,
                channel_name=channel_name,
                channel_url=channel_url
            )
        except Exception as e:
            logger.error(f"Error adding required channel: {e}")
            return False
    
    def remove_required_channel(self, channel_id):
        """Remove a required channel"""
        try:
            return self.required_channel_model.remove_channel(channel_id)
        except Exception as e:
            logger.error(f"Error removing required channel: {e}")
            return False
    
    def get_all_users(self):
        """Get all users"""
        try:
            return self.user_model.get_all_users()
        except Exception as e:
            logger.error(f"Error getting all users: {e}")
            return []
    
    def get_active_users(self, days=7):
        """Get active users in the last X days"""
        try:
            return self.user_model.get_active_users(days)
        except Exception as e:
            logger.error(f"Error getting active users: {e}")
            return []
    
    def get_vip_users(self):
        """Get all VIP users"""
        try:
            return self.user_model.get_vip_users()
        except Exception as e:
            logger.error(f"Error getting VIP users: {e}")
            return []
    
    def get_user_stats(self):
        """Get user statistics"""
        try:
            total_users = self.user_model.get_users_count()
            active_users = len(self.user_model.get_active_users(7))
            vip_users = len(self.user_model.get_vip_users())
            
            return {
                'total_users': total_users,
                'active_users': active_users,
                'vip_users': vip_users
            }
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            return None
    
    async def broadcast_message(self, bot, message_text, user_ids=None, rate_limit=20):
        """Broadcast a message to all users or specific users"""
        try:
            if not user_ids:
                # Get all users
                users = self.user_model.get_all_users()
                user_ids = [user['user_id'] for user in users]
            
            success_count = 0
            fail_count = 0
            
            # Send message to each user with rate limiting
            for i, user_id in enumerate(user_ids):
                try:
                    await bot.send_message(
                        chat_id=user_id,
                        text=message_text
                    )
                    success_count += 1
                except Exception as e:
                    logger.error(f"Error sending broadcast to user {user_id}: {e}")
                    fail_count += 1
                
                # Rate limiting to avoid Telegram limits
                if (i + 1) % rate_limit == 0:
                    await asyncio.sleep(1)  # Wait 1 second after every rate_limit messages
            
            return {
                'total': len(user_ids),
                'success': success_count,
                'fail': fail_count
            }
        except Exception as e:
            logger.error(f"Error broadcasting message: {e}")
            return None
    
    async def forward_message(self, bot, from_chat_id, message_id, user_ids=None, rate_limit=20):
        """Forward a message to all users or specific users"""
        try:
            if not user_ids:
                # Get all users
                users = self.user_model.get_all_users()
                user_ids = [user['user_id'] for user in users]
            
            success_count = 0
            fail_count = 0
            
            # Forward message to each user with rate limiting
            for i, user_id in enumerate(user_ids):
                try:
                    await bot.forward_message(
                        chat_id=user_id,
                        from_chat_id=from_chat_id,
                        message_id=message_id
                    )
                    success_count += 1
                except Exception as e:
                    logger.error(f"Error forwarding message to user {user_id}: {e}")
                    fail_count += 1
                
                # Rate limiting to avoid Telegram limits
                if (i + 1) % rate_limit == 0:
                    await asyncio.sleep(1)  # Wait 1 second after every rate_limit messages
            
            return {
                'total': len(user_ids),
                'success': success_count,
                'fail': fail_count
            }
        except Exception as e:
            logger.error(f"Error forwarding message: {e}")
            return None
