from database.db import Database

class User:
    """User model for managing user data"""
    
    def __init__(self, db):
        self.db = db
    
    def get_user(self, user_id):
        """Get user by Telegram user_id"""
        query = "SELECT * FROM users WHERE user_id = %s"
        return self.db.fetch_one(query, (user_id,))
    
    def create_user(self, user_id, username=None, first_name=None, last_name=None, is_admin=False):
        """Create a new user"""
        query = """
            INSERT INTO users (user_id, username, first_name, last_name, is_admin)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                username = VALUES(username),
                first_name = VALUES(first_name),
                last_name = VALUES(last_name)
        """
        params = (user_id, username, first_name, last_name, is_admin)
        return self.db.insert(query, params)
    
    def update_user(self, user_id, **kwargs):
        """Update user data"""
        allowed_fields = ['username', 'first_name', 'last_name', 'is_admin', 'daily_download_bytes', 'last_download_reset']
        
        # Filter out invalid fields
        update_data = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        if not update_data:
            return False
        
        # Build the SET part of the query
        set_clause = ", ".join([f"{field} = %s" for field in update_data.keys()])
        query = f"UPDATE users SET {set_clause} WHERE user_id = %s"
        
        # Build the parameters
        params = list(update_data.values())
        params.append(user_id)
        
        self.db.execute_query(query, tuple(params))
        return True
    
    def get_all_users(self):
        """Get all users"""
        query = "SELECT * FROM users"
        return self.db.fetch_all(query)
    
    def is_admin(self, user_id):
        """Check if user is an admin"""
        query = "SELECT is_admin FROM users WHERE user_id = %s"
        result = self.db.fetch_one(query, (user_id,))
        return result and result['is_admin']
    
    def update_download_usage(self, user_id, bytes_downloaded):
        """Update user's daily download usage"""
        # First, check if we need to reset the counter (new day)
        query = """
            UPDATE users 
            SET daily_download_bytes = CASE
                WHEN last_download_reset < CURDATE() THEN %s
                ELSE daily_download_bytes + %s
            END,
            last_download_reset = CURDATE()
            WHERE user_id = %s
        """
        self.db.execute_query(query, (bytes_downloaded, bytes_downloaded, user_id))
        
        # Return the updated user data
        return self.get_user(user_id)
    
    def get_download_usage(self, user_id):
        """Get user's current download usage"""
        query = """
            SELECT 
                daily_download_bytes,
                last_download_reset,
                CASE
                    WHEN last_download_reset < CURDATE() THEN 0
                    ELSE daily_download_bytes
                END as current_usage
            FROM users 
            WHERE user_id = %s
        """
        return self.db.fetch_one(query, (user_id,))


class VIPSubscription:
    """VIP Subscription model for managing user subscriptions"""
    
    def __init__(self, db):
        self.db = db
    
    def get_active_subscription(self, user_id):
        """Get user's active subscription if any"""
        query = """
            SELECT * FROM vip_subscriptions 
            WHERE user_id = %s AND end_date > NOW() 
            ORDER BY end_date DESC LIMIT 1
        """
        return self.db.fetch_one(query, (user_id,))
    
    def create_subscription(self, user_id, subscription_type, payment_amount, duration_days):
        """Create a new subscription"""
        query = """
            INSERT INTO vip_subscriptions 
            (user_id, subscription_type, payment_amount, end_date) 
            VALUES (%s, %s, %s, DATE_ADD(NOW(), INTERVAL %s DAY))
        """
        params = (user_id, subscription_type, payment_amount, duration_days)
        return self.db.insert(query, params)
    
    def extend_subscription(self, user_id, subscription_type, payment_amount, duration_days):
        """Extend an existing subscription or create a new one"""
        # Check if user has an active subscription
        active_sub = self.get_active_subscription(user_id)
        
        if active_sub:
            # Extend the existing subscription
            query = """
                UPDATE vip_subscriptions 
                SET end_date = DATE_ADD(end_date, INTERVAL %s DAY) 
                WHERE id = %s
            """
            self.db.execute_query(query, (duration_days, active_sub['id']))
            return active_sub['id']
        else:
            # Create a new subscription
            return self.create_subscription(user_id, subscription_type, payment_amount, duration_days)
    
    def is_vip(self, user_id):
        """Check if user has an active VIP subscription"""
        return self.get_active_subscription(user_id) is not None
    
    def get_all_active_subscriptions(self):
        """Get all active subscriptions"""
        query = "SELECT * FROM vip_subscriptions WHERE end_date > NOW()"
        return self.db.fetch_all(query)


class Playlist:
    """Playlist model for managing user playlists"""
    
    def __init__(self, db):
        self.db = db
    
    def create_playlist(self, user_id, name, description=None):
        """Create a new playlist"""
        query = """
            INSERT INTO playlists (user_id, name, description)
            VALUES (%s, %s, %s)
        """
        return self.db.insert(query, (user_id, name, description))
    
    def get_playlist(self, playlist_id):
        """Get playlist by ID"""
        query = "SELECT * FROM playlists WHERE id = %s"
        return self.db.fetch_one(query, (playlist_id,))
    
    def get_user_playlists(self, user_id):
        """Get all playlists for a user"""
        query = "SELECT * FROM playlists WHERE user_id = %s ORDER BY created_at DESC"
        return self.db.fetch_all(query, (user_id,))
    
    def update_playlist(self, playlist_id, name=None, description=None):
        """Update playlist details"""
        if name is None and description is None:
            return False
            
        query_parts = []
        params = []
        
        if name is not None:
            query_parts.append("name = %s")
            params.append(name)
            
        if description is not None:
            query_parts.append("description = %s")
            params.append(description)
            
        query = f"UPDATE playlists SET {', '.join(query_parts)} WHERE id = %s"
        params.append(playlist_id)
        
        self.db.execute_query(query, tuple(params))
        return True
    
    def delete_playlist(self, playlist_id):
        """Delete a playlist"""
        query = "DELETE FROM playlists WHERE id = %s"
        self.db.execute_query(query, (playlist_id,))
        return True
    
    def add_song_to_playlist(self, playlist_id, song_id):
        """Add a song to a playlist"""
        query = """
            INSERT INTO playlist_songs (playlist_id, song_id)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE added_at = NOW()
        """
        self.db.execute_query(query, (playlist_id, song_id))
        return True
    
    def remove_song_from_playlist(self, playlist_id, song_id):
        """Remove a song from a playlist"""
        query = "DELETE FROM playlist_songs WHERE playlist_id = %s AND song_id = %s"
        self.db.execute_query(query, (playlist_id, song_id))
        return True
    
    def get_playlist_songs(self, playlist_id):
        """Get all songs in a playlist"""
        query = """
            SELECT s.* FROM songs s
            JOIN playlist_songs ps ON s.id = ps.song_id
            WHERE ps.playlist_id = %s
            ORDER BY ps.added_at DESC
        """
        return self.db.fetch_all(query, (playlist_id,))


class Song:
    """Song model for managing music data"""
    
    def __init__(self, db):
        self.db = db
    
    def create_song(self, title, artist=None, platform=None, url=None, file_path=None, 
                   duration=None, language=None):
        """Create a new song record"""
        query = """
            INSERT INTO songs 
            (title, artist, platform, url, file_path, duration, language)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        params = (title, artist, platform, url, file_path, duration, language)
        return self.db.insert(query, params)
    
    def get_song(self, song_id):
        """Get song by ID"""
        query = "SELECT * FROM songs WHERE id = %s"
        return self.db.fetch_one(query, (song_id,))
    
    def get_song_by_url(self, url):
        """Get song by URL"""
        query = "SELECT * FROM songs WHERE url = %s"
        return self.db.fetch_one(query, (url,))
    
    def update_song(self, song_id, **kwargs):
        """Update song data"""
        allowed_fields = ['title', 'artist', 'platform', 'url', 'file_path', 
                         'duration', 'language', 'download_count']
        
        # Filter out invalid fields
        update_data = {k: v for k, v in kwargs.items() if k in allowed_fields}
        
        if not update_data:
            return False
        
        # Build the SET part of the query
        set_clause = ", ".join([f"{field} = %s" for field in update_data.keys()])
        query = f"UPDATE songs SET {set_clause} WHERE id = %s"
        
        # Build the parameters
        params = list(update_data.values())
        params.append(song_id)
        
        self.db.execute_query(query, tuple(params))
        return True
    
    def increment_download_count(self, song_id):
        """Increment the download count for a song"""
        query = "UPDATE songs SET download_count = download_count + 1 WHERE id = %s"
        self.db.execute_query(query, (song_id,))
        return True
    
    def get_popular_songs(self, limit=10, language=None):
        """Get popular songs based on download count"""
        query = "SELECT * FROM songs WHERE 1=1"
        params = []
        
        if language:
            query += " AND language = %s"
            params.append(language)
            
        query += " ORDER BY download_count DESC LIMIT %s"
        params.append(limit)
        
        return self.db.fetch_all(query, tuple(params))
    
    def get_new_songs(self, limit=10, language=None):
        """Get newest songs"""
        query = "SELECT * FROM songs WHERE 1=1"
        params = []
        
        if language:
            query += " AND language = %s"
            params.append(language)
            
        query += " ORDER BY added_at DESC LIMIT %s"
        params.append(limit)
        
        return self.db.fetch_all(query, tuple(params))


class DownloadHistory:
    """Download History model for tracking user downloads"""
    
    def __init__(self, db):
        self.db = db
    
    def add_download(self, user_id, content_type, content_url, file_size):
        """Add a download record"""
        query = """
            INSERT INTO download_history 
            (user_id, content_type, content_url, file_size)
            VALUES (%s, %s, %s, %s)
        """
        params = (user_id, content_type, content_url, file_size)
        return self.db.insert(query, params)
    
    def get_user_downloads(self, user_id, limit=10):
        """Get user's download history"""
        query = """
            SELECT * FROM download_history 
            WHERE user_id = %s 
            ORDER BY download_date DESC 
            LIMIT %s
        """
        return self.db.fetch_all(query, (user_id, limit))
    
    def get_user_daily_downloads(self, user_id):
        """Get user's downloads for today"""
        query = """
            SELECT SUM(file_size) as total_size 
            FROM download_history 
            WHERE user_id = %s AND DATE(download_date) = CURDATE()
        """
        result = self.db.fetch_one(query, (user_id,))
        return result['total_size'] if result and result['total_size'] else 0


class RequiredChannel:
    """Required Channel model for managing join requirements"""
    
    def __init__(self, db):
        self.db = db
    
    def add_channel(self, channel_id, channel_name, channel_url, added_by):
        """Add a required channel"""
        query = """
            INSERT INTO required_channels 
            (channel_id, channel_name, channel_url, added_by)
            VALUES (%s, %s, %s, %s)
        """
        params = (channel_id, channel_name, channel_url, added_by)
        return self.db.insert(query, params)
    
    def get_channel(self, channel_id):
        """Get channel by ID"""
        query = "SELECT * FROM required_channels WHERE channel_id = %s"
        return self.db.fetch_one(query, (channel_id,))
    
    def get_all_channels(self):
        """Get all required channels"""
        query = "SELECT * FROM required_channels"
        return self.db.fetch_all(query)
    
    def delete_channel(self, channel_id):
        """Delete a required channel"""
        query = "DELETE FROM required_channels WHERE channel_id = %s"
        self.db.execute_query(query, (channel_id,))
        return True
    
    def count_channels(self):
        """Count the number of required channels"""
        query = "SELECT COUNT(*) as count FROM required_channels"
        result = self.db.fetch_one(query)
        return result['count'] if result else 0
