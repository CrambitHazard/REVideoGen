import os
import requests
from typing import List, Dict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VideoScraper:
    def __init__(self):
        self.api_key = os.getenv('PEXELS_API_KEY')
        if not self.api_key:
            raise ValueError("Pexels API key not found in environment variables")
        self.base_url = "https://api.pexels.com/videos"
        
    def search_videos(self, query: str, per_page: int = 1) -> List[Dict]:
        """
        Search for videos matching the query on Pexels
        """
        try:
            headers = {
                'Authorization': self.api_key
            }
            
            params = {
                'query': query,
                'per_page': per_page,
                'orientation': 'landscape'  # Better for real estate videos
            }
            
            response = requests.get(
                f"{self.base_url}/search",
                headers=headers,
                params=params
            )
            response.raise_for_status()
            
            data = response.json()
            videos = data.get('videos', [])
            
            if not videos:
                logger.warning(f"No videos found for query: {query}")
                return []
            
            return [{
                'url': video['url'],
                'duration': video['duration'],
                'width': video['width'],
                'height': video['height'],
                'download_url': self._get_best_video_url(video)
            } for video in videos]
            
        except Exception as e:
            logger.error(f"Error searching videos: {str(e)}")
            return []
    
    def _get_best_video_url(self, video: Dict) -> str:
        """
        Get the highest quality video URL available
        """
        try:
            video_files = sorted(
                video['video_files'],
                key=lambda x: (x['width'] * x['height']),
                reverse=True
            )
            return video_files[0]['link'] if video_files else None
        except (KeyError, IndexError) as e:
            logger.error(f"Error getting video URL: {str(e)}")
            return None
    
    def download_video(self, video_url: str, save_path: str) -> str:
        """
        Download video from URL and save to specified path
        """
        try:
            if not video_url:
                raise ValueError("No valid video URL provided")
                
            response = requests.get(video_url, stream=True)
            response.raise_for_status()
            
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            logger.info(f"Video successfully downloaded to {save_path}")
            return save_path
        except Exception as e:
            logger.error(f"Error downloading video: {str(e)}")
            return None 