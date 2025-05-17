import os
import logging
from dotenv import load_dotenv
from heygen_integration import HeygenIntegration
from video_scraper import VideoScraper

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG for more detailed logging
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_video_generation():
    """Test complete video generation process"""
    try:
        # Load environment variables from .env file
        load_dotenv()
        
        # Create output directories
        os.makedirs('downloads', exist_ok=True)
        os.makedirs('output', exist_ok=True)
        
        # Step 1: Download a test video
        logger.info("Downloading test video...")
        scraper = VideoScraper()
        videos = scraper.search_videos("luxury living room", per_page=1)
        
        if not videos:
            logger.error("No videos found")
            return False
            
        video_data = videos[0]
        video_path = "downloads/test_video.mp4"
        downloaded_path = scraper.download_video(
            video_data['download_url'],
            video_path
        )
        
        if not downloaded_path:
            logger.error("Failed to download video")
            return False
            
        logger.info(f"Video downloaded to {downloaded_path}")
        
        # Step 2: Generate a test video
        logger.info("Creating Heygen video...")
        heygen = HeygenIntegration()
        
        # Test avatar and voice retrieval first
        logger.info("Testing avatar retrieval...")
        avatar_id = heygen._get_first_available_avatar()
        if avatar_id:
            logger.info(f"Successfully retrieved avatar ID: {avatar_id}")
        else:
            logger.error("Failed to retrieve avatar")
            return False
            
        logger.info("Testing voice retrieval...")
        voice_id = heygen._get_first_available_voice()
        if voice_id:
            logger.info(f"Successfully retrieved voice ID: {voice_id}")
        else:
            logger.error("Failed to retrieve voice")
            return False
        
        test_description = "Welcome to this stunning living room, where modern elegance meets comfort. The spacious layout and abundant natural light create an inviting atmosphere perfect for both relaxation and entertaining."
        
        result = heygen.create_video(
            video_path=downloaded_path,
            description=test_description
        )
        
        if result:
            logger.info("Video generation successful!")
            logger.info(f"Video URL: {result.get('video_url')}")
            logger.info(f"Thumbnail URL: {result.get('thumbnail_url')}")
            logger.info(f"Duration: {result.get('duration')} seconds")
            return True
        else:
            logger.error("Video generation failed")
            return False
            
    except Exception as e:
        logger.error(f"Error in test: {str(e)}")
        return False

if __name__ == "__main__":
    test_video_generation() 