import os
import time
import requests
import logging
from typing import Dict, Optional

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HeygenIntegration:
    def __init__(self):
        self.api_key = os.getenv('HEYGEN_API_KEY')
        if not self.api_key:
            raise ValueError("Heygen API key not found in environment variables")
        self.base_url = "https://api.heygen.com/v2"
        
    def create_video(self, 
                    video_path: str, 
                    description: str,
                    avatar_url: Optional[str] = None) -> Dict:
        """
        Create a video using Heygen API with the given stock video and description
        """
        try:
            # First, get available avatars and voices
            avatar_id = self._get_first_available_avatar()
            voice_id = self._get_first_available_voice()
            
            if not avatar_id or not voice_id:
                raise ValueError("Could not find available avatar or voice")
            
            logger.info(f"Using avatar ID: {avatar_id} and voice ID: {voice_id}")
            
            # Create the video generation task
            video_id = self._generate_video(
                avatar_id=avatar_id,
                voice_id=voice_id,
                text=description,
                background_video_path=video_path
            )
            
            if not video_id:
                raise ValueError("Failed to create video generation task")
            
            logger.info(f"Video generation task created with ID: {video_id}")
            
            # Wait for the video to be generated
            result = self._wait_for_completion(video_id)
            if result:
                logger.info("Video generation completed successfully")
            return result
            
        except Exception as e:
            logger.error(f"Error in video creation: {str(e)}")
            return None
    
    def _get_first_available_avatar(self) -> Optional[str]:
        """
        Get the first available avatar ID
        """
        try:
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "X-Api-Key": self.api_key
            }
            
            url = f"{self.base_url}/avatars"
            logger.info(f"Making request to: {url}")
            logger.info(f"Using headers: {headers}")
            
            response = requests.get(url, headers=headers)
            
            if response.status_code != 200:
                logger.error(f"API Error - Status Code: {response.status_code}")
                logger.error(f"Response Text: {response.text}")
                response.raise_for_status()
            
            data = response.json()
            logger.info(f"API Response: {data}")
            
            # Try different response formats
            avatars = None
            if 'data' in data:
                avatars = data.get('data', {}).get('avatars', []) or data.get('data', {}).get('list', [])
            
            if not avatars and 'avatars' in data:
                avatars = data.get('avatars', [])
                
            if avatars:
                return avatars[0].get('avatar_id')
            
            logger.error("No avatars found in response")
            return None
            
        except Exception as e:
            logger.error(f"Error getting avatars: {str(e)}")
            if 'response' in locals():
                logger.error(f"Response status code: {response.status_code}")
                logger.error(f"Response text: {response.text}")
            return None
    
    def _get_first_available_voice(self) -> Optional[str]:
        """
        Get the first available voice ID
        """
        try:
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "X-Api-Key": self.api_key
            }
            
            response = requests.get(
                f"{self.base_url}/voices",
                headers=headers
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Try different response formats
            voices = None
            if 'data' in data:
                voices = data.get('data', {}).get('voices', []) or data.get('data', {}).get('list', [])
            
            if not voices and 'voices' in data:
                voices = data.get('voices', [])
                
            if voices:
                return voices[0].get('voice_id')
            
            logger.error("No voices found in response")
            return None
            
        except Exception as e:
            logger.error(f"Error getting voices: {str(e)}")
            return None
    
    def _generate_video(self,
                       avatar_id: str,
                       voice_id: str,
                       text: str,
                       background_video_path: str) -> Optional[str]:
        """
        Generate a video using Heygen API
        """
        try:
            # First upload the background video
            video_url = self._upload_video(background_video_path)
            if not video_url:
                raise ValueError("Failed to upload background video")
            
            logger.info(f"Background video uploaded successfully: {video_url}")
            
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "X-Api-Key": self.api_key
            }
            
            data = {
                "video_inputs": [
                    {
                        "character": {
                            "type": "avatar",
                            "avatar_id": avatar_id,
                            "avatar_style": "normal"
                        },
                        "voice": {
                            "type": "text",
                            "input_text": text,
                            "voice_id": voice_id,
                            "speed": 1.0
                        },
                        "background": {
                            "type": "video",
                            "url": video_url
                        }
                    }
                ],
                "dimension": {
                    "width": 1920,
                    "height": 1080
                }
            }
            
            response = requests.post(
                f"{self.base_url}/video/generate",
                headers=headers,
                json=data
            )
            response.raise_for_status()
            
            result = response.json()
            video_id = result.get('data', {}).get('video_id')
            if not video_id:
                logger.error(f"No video ID in response: {result}")
            return video_id
            
        except Exception as e:
            logger.error(f"Error generating video: {str(e)}")
            return None
    
    def _upload_video(self, video_path: str) -> Optional[str]:
        """
        Upload a video to Heygen
        """
        try:
            if not os.path.exists(video_path):
                raise ValueError(f"Video file not found: {video_path}")
                
            headers = {
                "Accept": "application/json",
                "X-Api-Key": self.api_key
            }
                
            with open(video_path, 'rb') as f:
                files = {'file': f}
                response = requests.post(
                    f"{self.base_url}/upload/video",
                    headers=headers,
                    files=files
                )
                response.raise_for_status()
                
                result = response.json()
                return result.get('data', {}).get('url')
                
        except Exception as e:
            logger.error(f"Error uploading video: {str(e)}")
            return None
    
    def _wait_for_completion(self, video_id: str, timeout: int = 300) -> Optional[Dict]:
        """
        Wait for video generation to complete
        """
        try:
            start_time = time.time()
            while time.time() - start_time < timeout:
                headers = {
                    "Accept": "application/json",
                    "X-Api-Key": self.api_key
                }
                
                response = requests.get(
                    f"{self.base_url}/video/status?video_id={video_id}",
                    headers=headers
                )
                response.raise_for_status()
                
                data = response.json().get('data', {})
                status = data.get('status')
                
                if status == 'completed':
                    logger.info("Video generation completed successfully")
                    return data
                elif status == 'failed':
                    error = data.get('error', {})
                    error_msg = error.get('message', 'Unknown error')
                    logger.error(f"Video generation failed: {error_msg}")
                    return None
                
                logger.info(f"Video status: {status}. Waiting...")
                time.sleep(5)
            
            logger.error(f"Timeout waiting for video completion after {timeout} seconds")
            return None
            
        except Exception as e:
            logger.error(f"Error checking video status: {str(e)}")
            return None 