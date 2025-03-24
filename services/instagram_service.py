import os
import logging
import instaloader
import requests
import tempfile
import subprocess
import time
import random
from utils.helpers import sanitize_filename, create_download_dir
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class InstagramDownloader:
    """Service for downloading content from Instagram"""
    
    def __init__(self):
        self.loader = instaloader.Instaloader(
            download_videos=True,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            save_metadata=False,
            compress_json=False
        )
        # Set a user agent to avoid rate limiting
        self.loader.context.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        # Add a small delay between requests to avoid rate limiting
        self.loader.context.sleep = True
        # Increase delay between requests to avoid rate limiting
        self.loader.context.sleep_between_requests = 5
        # Set maximum number of connection attempts
        self.loader.context.max_connection_attempts = 3
        
        # Try to authenticate with Instagram if credentials are available
        self._authenticate()
        
        # Track failed attempts to implement exponential backoff
        self.failed_attempts = 0
        self.max_retries = 3
    
    def _authenticate(self):
        """Authenticate with Instagram using credentials from environment variables"""
        try:
            username = os.getenv('INSTAGRAM_USERNAME')
            password = os.getenv('INSTAGRAM_PASSWORD')
            
            if username and password:
                logger.info(f"Attempting to login to Instagram as {username}")
                self.loader.login(username, password)
                logger.info("Instagram login successful")
                
                # Save session for future use
                session_file = os.getenv('INSTAGRAM_SESSION_FILE', 'instagram_session')
                self.loader.save_session_to_file(session_file)
            else:
                # Try to load session if available
                session_file = os.getenv('INSTAGRAM_SESSION_FILE', 'instagram_session')
                if os.path.exists(session_file):
                    logger.info(f"Loading Instagram session from {session_file}")
                    try:
                        self.loader.load_session_from_file(username, session_file)
                        logger.info("Instagram session loaded successfully")
                    except Exception as e:
                        logger.warning(f"Failed to load Instagram session: {e}")
                else:
                    logger.warning("No Instagram credentials or session file found. Some downloads may fail due to rate limiting.")
        except Exception as e:
            logger.error(f"Instagram authentication error: {e}")
            logger.warning("Continuing without authentication. Some downloads may fail.")
    
    def _handle_rate_limiting(self, operation_name):
        """Handle rate limiting with exponential backoff"""
        if self.failed_attempts > 0:
            # Calculate backoff time with jitter
            backoff_time = min(30, 2 ** self.failed_attempts) + random.uniform(0, 1)
            logger.warning(f"Rate limiting detected for {operation_name}. Backing off for {backoff_time:.2f} seconds (attempt {self.failed_attempts}/{self.max_retries})")
            time.sleep(backoff_time)
        
        self.failed_attempts += 1
        return self.failed_attempts <= self.max_retries
    
    def _reset_rate_limiting(self):
        """Reset rate limiting counter after successful operation"""
        self.failed_attempts = 0
    
    def download_post(self, post_url, output_dir):
        """Download Instagram post (photo or video)"""
        try:
            # Extract shortcode from URL
            shortcode = post_url.split("/p/")[1].split("/")[0]
            if "?" in shortcode:
                shortcode = shortcode.split("?")[0]
            
            # Get post by shortcode
            post = instaloader.Post.from_shortcode(self.loader.context, shortcode)
            
            # Create temporary directory for download
            with tempfile.TemporaryDirectory() as temp_dir:
                # Download post
                self.loader.download_post(post, target=temp_dir)
                
                # Find downloaded files
                files = os.listdir(temp_dir)
                
                # Get video file if exists
                video_files = [f for f in files if f.endswith('.mp4')]
                if video_files:
                    video_path = os.path.join(temp_dir, video_files[0])
                    output_video_path = os.path.join(output_dir, f"{sanitize_filename(post.owner_username)}_{shortcode}.mp4")
                    
                    # Copy file to output directory
                    with open(video_path, 'rb') as src, open(output_video_path, 'wb') as dst:
                        dst.write(src.read())
                    
                    # Reset rate limiting counter after success
                    self._reset_rate_limiting()
                    
                    return {
                        'type': 'video',
                        'file_path': output_video_path,
                        'caption': post.caption if post.caption else '',
                        'owner': post.owner_username,
                        'likes': post.likes,
                        'date': post.date_local.strftime('%Y-%m-%d %H:%M:%S')
                    }
                
                # Get image file if exists
                image_files = [f for f in files if f.endswith('.jpg')]
                if image_files:
                    image_path = os.path.join(temp_dir, image_files[0])
                    output_image_path = os.path.join(output_dir, f"{sanitize_filename(post.owner_username)}_{shortcode}.jpg")
                    
                    # Copy file to output directory
                    with open(image_path, 'rb') as src, open(output_image_path, 'wb') as dst:
                        dst.write(src.read())
                    
                    # Reset rate limiting counter after success
                    self._reset_rate_limiting()
                    
                    return {
                        'type': 'photo',
                        'file_path': output_image_path,
                        'caption': post.caption if post.caption else '',
                        'owner': post.owner_username,
                        'likes': post.likes,
                        'date': post.date_local.strftime('%Y-%m-%d %H:%M:%S')
                    }
            
            return None
        except instaloader.exceptions.ConnectionException as e:
            logger.error(f"Connection error downloading Instagram post: {e}")
            if self._handle_rate_limiting("post download"):
                logger.info(f"Retrying post download for {post_url}")
                return self.download_post(post_url, output_dir)
            return None
        except Exception as e:
            logger.error(f"Error downloading Instagram post: {e}")
            return None
    
    def download_reel(self, reel_url, output_dir):
        """Download Instagram reel"""
        try:
            # Extract shortcode from URL
            if "/reel/" in reel_url:
                shortcode = reel_url.split("/reel/")[1].split("/")[0]
            else:
                # Handle old format URLs
                shortcode = reel_url.split("/p/")[1].split("/")[0]
            
            # Remove query parameters if present
            if "?" in shortcode:
                shortcode = shortcode.split("?")[0]
            
            # Get post by shortcode
            post = instaloader.Post.from_shortcode(self.loader.context, shortcode)
            
            # Create temporary directory for download
            with tempfile.TemporaryDirectory() as temp_dir:
                # Download post
                self.loader.download_post(post, target=temp_dir)
                
                # Find downloaded files
                files = os.listdir(temp_dir)
                
                # Get video file
                video_files = [f for f in files if f.endswith('.mp4')]
                if video_files:
                    video_path = os.path.join(temp_dir, video_files[0])
                    output_video_path = os.path.join(output_dir, f"{sanitize_filename(post.owner_username)}_reel_{shortcode}.mp4")
                    
                    # Copy file to output directory
                    with open(video_path, 'rb') as src, open(output_video_path, 'wb') as dst:
                        dst.write(src.read())
                    
                    # Create audio version
                    output_audio_path = os.path.join(output_dir, f"{sanitize_filename(post.owner_username)}_reel_{shortcode}.mp3")
                    
                    # Use ffmpeg to extract audio
                    try:
                        subprocess.run([
                            'ffmpeg', '-i', output_video_path, '-q:a', '0', '-map', 'a', output_audio_path, '-y'
                        ], check=True, capture_output=True)
                    except Exception as e:
                        logger.error(f"Error extracting audio from reel: {e}")
                        output_audio_path = None
                    
                    # Reset rate limiting counter after success
                    self._reset_rate_limiting()
                    
                    return {
                        'type': 'reel',
                        'file_path': output_video_path,
                        'audio_path': output_audio_path,
                        'caption': post.caption if post.caption else '',
                        'owner': post.owner_username,
                        'likes': post.likes,
                        'date': post.date_local.strftime('%Y-%m-%d %H:%M:%S')
                    }
            
            return None
        except instaloader.exceptions.ConnectionException as e:
            logger.error(f"Connection error downloading Instagram reel: {e}")
            if self._handle_rate_limiting("reel download"):
                logger.info(f"Retrying reel download for {reel_url}")
                return self.download_reel(reel_url, output_dir)
            return None
        except Exception as e:
            logger.error(f"Error downloading Instagram reel: {e}")
            return None
    
    def download_story(self, story_url, output_dir):
        """Download Instagram story"""
        try:
            # Extract username and story ID from URL
            # Format: https://www.instagram.com/stories/username/12345678901234567/
            parts = story_url.strip('/').split('/')
            username = parts[-3]
            story_id = parts[-2]
            
            # Get profile
            profile = instaloader.Profile.from_username(self.loader.context, username)
            
            # Create temporary directory for download
            with tempfile.TemporaryDirectory() as temp_dir:
                # Download stories
                self.loader.download_stories(userids=[profile.userid], filename_target=temp_dir)
                
                # Find downloaded files
                story_dir = os.path.join(temp_dir, username)
                if not os.path.exists(story_dir):
                    logger.error(f"Story directory not found: {story_dir}")
                    return None
                
                files = os.listdir(story_dir)
                
                # Find the specific story by ID
                story_files = [f for f in files if story_id in f]
                if not story_files:
                    logger.error(f"Story file not found for ID: {story_id}")
                    # Try to get the most recent story instead
                    if files:
                        story_files = [files[0]]
                        logger.info(f"Using most recent story instead: {story_files[0]}")
                    else:
                        return None
                
                story_file = story_files[0]
                story_path = os.path.join(story_dir, story_file)
                
                # Determine file type
                is_video = story_file.endswith('.mp4')
                output_file_path = os.path.join(
                    output_dir, 
                    f"{sanitize_filename(username)}_story_{story_id}.{'mp4' if is_video else 'jpg'}"
                )
                
                # Copy file to output directory
                with open(story_path, 'rb') as src, open(output_file_path, 'wb') as dst:
                    dst.write(src.read())
                
                # Create audio version if it's a video
                output_audio_path = None
                if is_video:
                    output_audio_path = os.path.join(output_dir, f"{sanitize_filename(username)}_story_{story_id}.mp3")
                    
                    # Use ffmpeg to extract audio
                    try:
                        subprocess.run([
                            'ffmpeg', '-i', output_file_path, '-q:a', '0', '-map', 'a', output_audio_path, '-y'
                        ], check=True, capture_output=True)
                    except Exception as e:
                        logger.error(f"Error extracting audio from story: {e}")
                        output_audio_path = None
                
                # Reset rate limiting counter after success
                self._reset_rate_limiting()
                
                return {
                    'type': 'story',
                    'file_path': output_file_path,
                    'audio_path': output_audio_path if is_video else None,
                    'is_video': is_video,
                    'owner': username,
                    'date': ''  # Stories don't have accessible date info
                }
            
            return None
        except instaloader.exceptions.ConnectionException as e:
            logger.error(f"Connection error downloading Instagram story: {e}")
            if self._handle_rate_limiting("story download"):
                logger.info(f"Retrying story download for {story_url}")
                return self.download_story(story_url, output_dir)
            return None
        except Exception as e:
            logger.error(f"Error downloading Instagram story: {e}")
            return None
    
    def download_profile_pic(self, profile_url, output_dir):
        """Download Instagram profile picture"""
        try:
            # Extract username from URL
            username = profile_url.strip('/').split('/')[-1]
            if "?" in username:
                username = username.split("?")[0]
            
            # Get profile
            profile = instaloader.Profile.from_username(self.loader.context, username)
            
            # Get profile pic URL
            profile_pic_url = profile.profile_pic_url
            
            # Download profile pic
            response = requests.get(profile_pic_url)
            if response.status_code != 200:
                logger.error(f"Failed to download profile pic: {response.status_code}")
                return None
            
            # Save to file
            output_file_path = os.path.join(output_dir, f"{sanitize_filename(username)}_profile.jpg")
            with open(output_file_path, 'wb') as f:
                f.write(response.content)
            
            # Reset rate limiting counter after success
            self._reset_rate_limiting()
            
            return {
                'type': 'profile',
                'file_path': output_file_path,
                'owner': username
            }
        except instaloader.exceptions.ConnectionException as e:
            logger.error(f"Connection error downloading Instagram profile picture: {e}")
            if self._handle_rate_limiting("profile download"):
                logger.info(f"Retrying profile download for {profile_url}")
                return self.download_profile_pic(profile_url, output_dir)
            return None
        except Exception as e:
            logger.error(f"Error downloading Instagram profile picture: {e}")
            return None

class InstagramDownloadService:
    """Service for downloading content from Instagram"""
    
    def __init__(self):
        self.downloader = InstagramDownloader()
    
    def download_from_url(self, url, user_id, download_dir):
        """Download content from Instagram URL"""
        # Create user download directory
        user_download_dir = create_download_dir(download_dir, user_id)
        
        # Clean URL (remove tracking parameters)
        url = url.split("?")[0] if "?" in url else url
        
        # Determine content type from URL
        if '/p/' in url:
            return self.downloader.download_post(url, user_download_dir)
        elif '/reel/' in url:
            return self.downloader.download_reel(url, user_download_dir)
        elif '/stories/' in url:
            return self.downloader.download_story(url, user_download_dir)
        else:
            # Assume it's a profile URL
            return self.downloader.download_profile_pic(url, user_download_dir)
    
    def convert_to_mp3(self, video_path, output_dir=None):
        """Convert video to MP3 audio"""
        if not output_dir:
            output_dir = os.path.dirname(video_path)
        
        base_name = os.path.splitext(os.path.basename(video_path))[0]
        output_path = os.path.join(output_dir, f"{base_name}.mp3")
        
        try:
            subprocess.run([
                'ffmpeg', '-i', video_path, '-q:a', '0', '-map', 'a', output_path, '-y'
            ], check=True, capture_output=True)
            
            return output_path
        except Exception as e:
            logger.error(f"Error converting video to MP3: {e}")
            return None
