import os
import logging
from dotenv import load_dotenv
from video_scraper import VideoScraper
from gpt_description import DescriptionGenerator
from heygen_integration import HeygenIntegration

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RealEstateVideoPipeline:
    def __init__(self):
        # Check for API keys
        heygen_api_key = os.getenv('HEYGEN_API_KEY')
        if not heygen_api_key:
            raise ValueError("HEYGEN_API_KEY not found in environment variables")
            
        pexels_api_key = os.getenv('PEXELS_API_KEY')
        if not pexels_api_key:
            raise ValueError("PEXELS_API_KEY not found in environment variables")

        self.video_scraper = VideoScraper()
        self.description_generator = DescriptionGenerator()
        self.heygen_integration = HeygenIntegration()
        
        # Create output directories
        os.makedirs('downloads', exist_ok=True)
        os.makedirs('output', exist_ok=True)
    
    def process_room(self, room_type: str, features: list) -> dict:
        """
        Process a single room through the pipeline
        """
        try:
            # Step 1: Search and download stock video
            logger.info(f"Searching for {room_type} video...")
            # Simplify search query to increase chances of finding matches
            search_query = f"luxury {room_type}"
            videos = self.video_scraper.search_videos(search_query)
            
            if not videos:
                raise ValueError(f"No videos found for {room_type}")
            
            video_data = videos[0]
            video_path = f"downloads/{room_type.replace(' ', '_')}.mp4"
            downloaded_path = self.video_scraper.download_video(
                video_data['download_url'],
                video_path
            )
            
            if not downloaded_path:
                raise ValueError(f"Failed to download video for {room_type}")
            
            # Step 2: Generate description
            logger.info(f"Generating description for {room_type}...")
            description = self.description_generator.generate_description(
                room_type,
                features
            )
            
            if not description:
                raise ValueError(f"Failed to generate description for {room_type}")
            
            # Step 3: Create Heygen video
            logger.info(f"Creating Heygen video for {room_type}...")
            result = self.heygen_integration.create_video(
                video_path=downloaded_path,
                description=description
            )
            
            if not result:
                raise ValueError(f"Failed to create Heygen video for {room_type}")
            
            return {
                'room_type': room_type,
                'features': features,
                'description': description,
                'video_url': result.get('video_url'),
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"Error processing {room_type}: {str(e)}")
            return {
                'room_type': room_type,
                'features': features,
                'status': 'failed',
                'error': str(e)
            }

def main():
    # Example usage
    pipeline = RealEstateVideoPipeline()
    
    # Process multiple rooms with simpler search terms
    rooms = [
        {
            'type': 'living room',
            'features': ['spacious', 'modern', 'bright']
        },
        {
            'type': 'garden',
            'features': ['private', 'landscaped', 'peaceful']
        }
    ]
    
    results = []
    for room in rooms:
        result = pipeline.process_room(room['type'], room['features'])
        results.append(result)
        
        if result['status'] == 'success':
            logger.info(f"Successfully processed {room['type']}")
            logger.info(f"Video URL: {result.get('video_url')}")
        else:
            logger.error(f"Failed to process {room['type']}")
            logger.error(f"Error: {result.get('error')}")

if __name__ == "__main__":
    main() 