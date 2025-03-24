import os
import logging
import instaloader
import requests
import tempfile
import subprocess
from utils.helpers import sanitize_filename, create_download_dir

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
                    
                    return {
                        'type': 'photo',
                        'file_path': output_image_path,
                        'caption': post.caption if post.caption else '',
                        'owner': post.owner_username,
                        'likes': post.likes,
                        'date': post.date_local.strftime('%Y-%m-%d %H:%M:%S')
                    }
            
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
                
                return {
                    'type': 'story',
                    'file_path': output_file_path,
                    'audio_path': output_audio_path if is_video else None,
                    'is_video': is_video,
                    'owner': username,
                    'date': ''  # Stories don't have accessible date info
                }
            
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
            
            return {
                'type': 'profile',
                'file_path': output_file_path,
                'username': username,
                'full_name': profile.full_name,
                'biography': profile.biography,
                'followers': profile.followers,
                'followees': profile.followees
            }
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
