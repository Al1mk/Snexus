import logging
import os
from logging.handlers import RotatingFileHandler

def setup_logger(name, log_file, level=logging.INFO):
    """Function to setup a logger with file and console handlers"""
    # Create logs directory if it doesn't exist
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Create file handler for logging to a file
    file_handler = RotatingFileHandler(log_file, maxBytes=10*1024*1024, backupCount=5)
    file_handler.setFormatter(formatter)
    
    # Create console handler for logging to console
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

def get_file_size(file_path):
    """Get file size in bytes"""
    try:
        return os.path.getsize(file_path)
    except (FileNotFoundError, OSError):
        return 0

def format_size(size_bytes):
    """Format size in bytes to human-readable format"""
    if size_bytes == 0:
        return "0B"
    
    size_names = ("B", "KB", "MB", "GB", "TB")
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024
        i += 1
    
    return f"{size_bytes:.2f} {size_names[i]}"

def sanitize_filename(filename):
    """Sanitize filename to remove invalid characters"""
    # Replace invalid characters with underscore
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Limit filename length
    if len(filename) > 200:
        name, ext = os.path.splitext(filename)
        filename = name[:200] + ext
    
    return filename

def create_download_dir(base_dir, user_id):
    """Create user-specific download directory"""
    user_dir = os.path.join(base_dir, f"user_{user_id}")
    os.makedirs(user_dir, exist_ok=True)
    return user_dir

def is_valid_url(url):
    """Basic URL validation"""
    return url and (url.startswith('http://') or url.startswith('https://'))

def extract_platform_from_url(url):
    """Extract platform name from URL"""
    if not url:
        return None
    
    url = url.lower()
    
    if 'spotify.com' in url:
        return 'spotify'
    elif 'music.apple.com' in url:
        return 'apple_music'
    elif 'soundcloud.com' in url:
        return 'soundcloud'
    elif 'youtube.com' in url or 'youtu.be' in url:
        return 'youtube'
    elif 'instagram.com' in url:
        return 'instagram'
    else:
        return 'other'

def is_playlist_url(url, platform=None):
    """Check if URL is a playlist URL"""
    if not url:
        return False
    
    url = url.lower()
    platform = platform or extract_platform_from_url(url)
    
    if platform == 'spotify':
        return 'playlist' in url
    elif platform == 'apple_music':
        return 'playlist' in url
    elif platform == 'soundcloud':
        return 'sets' in url
    elif platform == 'youtube':
        return 'playlist' in url or 'list=' in url
    else:
        return False
