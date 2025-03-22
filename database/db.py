import mysql.connector
from mysql.connector import Error
from config.config import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME
import logging

logger = logging.getLogger(__name__)

class Database:
    """Database connection and operations class"""
    
    def __init__(self):
        self.connection = None
        self.connect()
    
    def connect(self):
        """Connect to MySQL database"""
        try:
            self.connection = mysql.connector.connect(
                host=DB_HOST,
                user=DB_USER,
                password=DB_PASSWORD,
                database=DB_NAME
            )
            if self.connection.is_connected():
                logger.info("Connected to MySQL database")
        except Error as e:
            logger.error(f"Error connecting to MySQL database: {e}")
    
    def execute_query(self, query, params=None):
        """Execute a query with optional parameters"""
        try:
            if not self.connection or not self.connection.is_connected():
                self.connect()
                
            cursor = self.connection.cursor(dictionary=True)
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
                
            self.connection.commit()
            return cursor
        except Error as e:
            logger.error(f"Error executing query: {e}")
            return None
    
    def fetch_all(self, query, params=None):
        """Execute a query and fetch all results"""
        cursor = self.execute_query(query, params)
        if cursor:
            result = cursor.fetchall()
            cursor.close()
            return result
        return []
    
    def fetch_one(self, query, params=None):
        """Execute a query and fetch one result"""
        cursor = self.execute_query(query, params)
        if cursor:
            result = cursor.fetchone()
            cursor.close()
            return result
        return None
    
    def insert(self, query, params=None):
        """Execute an insert query and return last row id"""
        cursor = self.execute_query(query, params)
        if cursor:
            last_id = cursor.lastrowid
            cursor.close()
            return last_id
        return None
    
    def close(self):
        """Close the database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("MySQL connection closed")
    
    def create_tables(self):
        """Create all required tables if they don't exist"""
        try:
            # Users table
            self.execute_query("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id BIGINT UNIQUE NOT NULL,
                    username VARCHAR(255),
                    first_name VARCHAR(255),
                    last_name VARCHAR(255),
                    join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_admin BOOLEAN DEFAULT FALSE,
                    daily_download_bytes BIGINT DEFAULT 0,
                    last_download_reset DATE
                )
            """)
            
            # VIP Subscriptions table
            self.execute_query("""
                CREATE TABLE IF NOT EXISTS vip_subscriptions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    end_date TIMESTAMP NOT NULL,
                    subscription_type ENUM('one_month', 'three_month') NOT NULL,
                    payment_amount INT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
            """)
            
            # Playlists table
            self.execute_query("""
                CREATE TABLE IF NOT EXISTS playlists (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
            """)
            
            # Songs table
            self.execute_query("""
                CREATE TABLE IF NOT EXISTS songs (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    artist VARCHAR(255),
                    platform VARCHAR(50),
                    url TEXT,
                    file_path VARCHAR(255),
                    duration INT,
                    language ENUM('persian', 'english', 'turkish', 'arabic', 'other') DEFAULT 'other',
                    download_count INT DEFAULT 0,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Playlist Songs (junction table)
            self.execute_query("""
                CREATE TABLE IF NOT EXISTS playlist_songs (
                    playlist_id INT NOT NULL,
                    song_id INT NOT NULL,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (playlist_id, song_id),
                    FOREIGN KEY (playlist_id) REFERENCES playlists(id) ON DELETE CASCADE,
                    FOREIGN KEY (song_id) REFERENCES songs(id) ON DELETE CASCADE
                )
            """)
            
            # Downloads History table
            self.execute_query("""
                CREATE TABLE IF NOT EXISTS download_history (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    content_type ENUM('music', 'video', 'instagram', 'youtube') NOT NULL,
                    content_url TEXT NOT NULL,
                    file_size BIGINT,
                    download_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                )
            """)
            
            # Required Channels table
            self.execute_query("""
                CREATE TABLE IF NOT EXISTS required_channels (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    channel_id VARCHAR(255) NOT NULL,
                    channel_name VARCHAR(255),
                    channel_url VARCHAR(255) NOT NULL,
                    added_by BIGINT NOT NULL,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (added_by) REFERENCES users(user_id) ON DELETE CASCADE
                )
            """)
            
            logger.info("All tables created successfully")
            return True
        except Error as e:
            logger.error(f"Error creating tables: {e}")
            return False
