import os
import sys
import logging
from dotenv import load_dotenv
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.instagram_service import InstagramDownloadService

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def test_instagram_download():
    """Test Instagram download functionality"""
    # Create test directory
    test_dir = os.path.join(os.getcwd(), 'tests', 'test_downloads')
    os.makedirs(test_dir, exist_ok=True)
    
    # Initialize service
    instagram_service = InstagramDownloadService()
    
    # Test URLs
    test_urls = [
        # Reel URL (the one that was failing)
        "https://www.instagram.com/reel/C4FYWpGOUAP/",
        # Post URL
        "https://www.instagram.com/p/C4Hl1-xvRVn/",
        # Profile URL
        "https://www.instagram.com/instagram/"
    ]
    
    # Test each URL
    for url in test_urls:
        logger.info(f"Testing URL: {url}")
        try:
            result = instagram_service.download_from_url(url, "test_user", test_dir)
            if result:
                logger.info(f"✅ Successfully downloaded content from {url}")
                logger.info(f"Type: {result['type']}")
                logger.info(f"File path: {result['file_path']}")
                
                # Check if file exists
                if os.path.exists(result['file_path']):
                    file_size = os.path.getsize(result['file_path'])
                    logger.info(f"File size: {file_size} bytes")
                else:
                    logger.error(f"❌ File does not exist: {result['file_path']}")
                
                # Check audio path if applicable
                if 'audio_path' in result and result['audio_path']:
                    if os.path.exists(result['audio_path']):
                        audio_size = os.path.getsize(result['audio_path'])
                        logger.info(f"Audio file size: {audio_size} bytes")
                    else:
                        logger.error(f"❌ Audio file does not exist: {result['audio_path']}")
            else:
                logger.error(f"❌ Failed to download content from {url}")
        except Exception as e:
            logger.error(f"❌ Error testing URL {url}: {e}")
    
    logger.info("Instagram download tests completed")

if __name__ == "__main__":
    test_instagram_download()
