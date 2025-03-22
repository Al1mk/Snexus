import logging
import datetime
from models.models import VIPSubscription, User

logger = logging.getLogger(__name__)

class VIPService:
    """Service for managing VIP subscriptions"""
    
    def __init__(self, db):
        self.db = db
        self.vip_model = VIPSubscription(db)
        self.user_model = User(db)
    
    def get_subscription(self, user_id):
        """Get active subscription for a user"""
        try:
            return self.vip_model.get_active_subscription(user_id)
        except Exception as e:
            logger.error(f"Error getting subscription: {e}")
            return None
    
    def is_vip(self, user_id):
        """Check if user has active VIP subscription"""
        try:
            return self.vip_model.is_vip(user_id)
        except Exception as e:
            logger.error(f"Error checking VIP status: {e}")
            return False
    
    def create_subscription(self, user_id, subscription_type, payment_amount, payment_method="card", payment_ref=None):
        """Create a new VIP subscription"""
        try:
            # Calculate subscription duration
            if subscription_type == "one_month":
                duration_days = 30
            elif subscription_type == "three_month":
                duration_days = 90
            else:
                logger.error(f"Invalid subscription type: {subscription_type}")
                return None
            
            # Calculate end date
            start_date = datetime.datetime.now()
            end_date = start_date + datetime.timedelta(days=duration_days)
            
            # Create subscription
            subscription_id = self.vip_model.create_subscription(
                user_id=user_id,
                subscription_type=subscription_type,
                start_date=start_date,
                end_date=end_date,
                payment_amount=payment_amount,
                payment_method=payment_method,
                payment_ref=payment_ref
            )
            
            if subscription_id:
                return {
                    'id': subscription_id,
                    'user_id': user_id,
                    'subscription_type': subscription_type,
                    'start_date': start_date,
                    'end_date': end_date,
                    'payment_amount': payment_amount,
                    'payment_method': payment_method,
                    'payment_ref': payment_ref
                }
            
            return None
        except Exception as e:
            logger.error(f"Error creating subscription: {e}")
            return None
    
    def extend_subscription(self, user_id, subscription_type, payment_amount, payment_method="card", payment_ref=None):
        """Extend an existing VIP subscription"""
        try:
            # Get current subscription
            current_subscription = self.vip_model.get_active_subscription(user_id)
            
            # Calculate subscription duration
            if subscription_type == "one_month":
                duration_days = 30
            elif subscription_type == "three_month":
                duration_days = 90
            else:
                logger.error(f"Invalid subscription type: {subscription_type}")
                return None
            
            # Calculate new end date
            if current_subscription:
                # Extend from current end date
                start_date = current_subscription['end_date']
            else:
                # New subscription
                start_date = datetime.datetime.now()
            
            end_date = start_date + datetime.timedelta(days=duration_days)
            
            # Create subscription
            subscription_id = self.vip_model.create_subscription(
                user_id=user_id,
                subscription_type=subscription_type,
                start_date=start_date,
                end_date=end_date,
                payment_amount=payment_amount,
                payment_method=payment_method,
                payment_ref=payment_ref
            )
            
            if subscription_id:
                return {
                    'id': subscription_id,
                    'user_id': user_id,
                    'subscription_type': subscription_type,
                    'start_date': start_date,
                    'end_date': end_date,
                    'payment_amount': payment_amount,
                    'payment_method': payment_method,
                    'payment_ref': payment_ref
                }
            
            return None
        except Exception as e:
            logger.error(f"Error extending subscription: {e}")
            return None
    
    def cancel_subscription(self, subscription_id, user_id):
        """Cancel a VIP subscription"""
        try:
            # Check if subscription exists and belongs to user
            subscription = self.vip_model.get_subscription(subscription_id)
            if not subscription:
                logger.error(f"Subscription not found: {subscription_id}")
                return False
            
            if subscription['user_id'] != user_id:
                logger.error(f"Subscription {subscription_id} does not belong to user {user_id}")
                return False
            
            # Cancel subscription
            return self.vip_model.cancel_subscription(subscription_id)
        except Exception as e:
            logger.error(f"Error canceling subscription: {e}")
            return False
    
    def get_all_subscriptions(self, user_id):
        """Get all subscriptions for a user"""
        try:
            return self.vip_model.get_user_subscriptions(user_id)
        except Exception as e:
            logger.error(f"Error getting user subscriptions: {e}")
            return []
    
    def get_subscription_details(self, subscription_id):
        """Get details of a subscription"""
        try:
            return self.vip_model.get_subscription(subscription_id)
        except Exception as e:
            logger.error(f"Error getting subscription details: {e}")
            return None
    
    def verify_payment(self, payment_ref, expected_amount):
        """Verify payment (placeholder for actual payment verification)"""
        try:
            # In a real implementation, this would verify the payment with a payment gateway
            # For now, we'll just return True
            logger.info(f"Verifying payment: {payment_ref}, amount: {expected_amount}")
            return True
        except Exception as e:
            logger.error(f"Error verifying payment: {e}")
            return False
    
    def get_vip_users_count(self):
        """Get count of users with active VIP subscription"""
        try:
            return self.vip_model.get_vip_users_count()
        except Exception as e:
            logger.error(f"Error getting VIP users count: {e}")
            return 0
    
    def get_subscription_stats(self):
        """Get subscription statistics"""
        try:
            total_subscriptions = self.vip_model.get_total_subscriptions_count()
            active_subscriptions = self.vip_model.get_active_subscriptions_count()
            one_month_subscriptions = self.vip_model.get_subscription_type_count("one_month")
            three_month_subscriptions = self.vip_model.get_subscription_type_count("three_month")
            total_revenue = self.vip_model.get_total_revenue()
            
            return {
                'total_subscriptions': total_subscriptions,
                'active_subscriptions': active_subscriptions,
                'one_month_subscriptions': one_month_subscriptions,
                'three_month_subscriptions': three_month_subscriptions,
                'total_revenue': total_revenue
            }
        except Exception as e:
            logger.error(f"Error getting subscription stats: {e}")
            return None
