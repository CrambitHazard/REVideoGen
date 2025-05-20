import os
import time
import requests
import logging
from typing import Dict, Optional, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HeygenIntegration:
    def __init__(self):
        self.api_key = os.getenv('HEYGEN_API_KEY')
        if not self.api_key:
            raise ValueError("Heygen API key not found in environment variables")
        self.base_url = "https://api.heygen.com/v2"
        self.upload_url = "https://upload.heygen.com/v1/asset"
        self.headers = {
            "Accept": "application/json",
            "X-Api-Key": self.api_key
        }

    def _make_api_request(self, method: str, endpoint: str, json_payload: Optional[Dict] = None, params: Optional[Dict] = None) -> Optional[Dict]:
        """
        Makes an API request to the specified endpoint.
        """
        url = f"{self.base_url}/{endpoint}"
        try:
            headers = self.headers.copy()
            if method.upper() == "POST":
                headers["Content-Type"] = "application/json"

            if method.upper() == "GET":
                response = requests.get(url, headers=headers, params=params)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=json_payload)
            else:
                logger.error(f"Unsupported HTTP method: {method}")
                return None

            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as http_err:
            logger.error(f"HTTP error occurred: {http_err}")
            if 'response' in locals():
                logger.error(f"Response content: {response.content.decode()}")
        except requests.exceptions.RequestException as req_err:
            logger.error(f"Request error occurred: {req_err}")
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
        return None

    def _get_first_available_avatar(self) -> Optional[str]:
        """
        Get the first available avatar ID
        """
        try:
            response = requests.get(f"{self.base_url}/avatars", headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            if data and "data" in data and "avatars" in data["data"]:
                avatars = data["data"]["avatars"]
                if avatars:
                    avatar_id = avatars[0].get('avatar_id')
                    logger.info(f"Selected avatar: {avatar_id}")
                    return avatar_id
            
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
            response = requests.get(f"{self.base_url}/voices", headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            if data and "data" in data and "voices" in data["data"]:
                voices = data["data"]["voices"]
                if voices:
                    # Try to find an English voice first
                    english_voice = next((v['voice_id'] for v in voices if v.get('language_code','').startswith('en')), None)
                    voice_id = english_voice if english_voice else voices[0].get('voice_id')
                    logger.info(f"Selected voice: {voice_id}")
                    return voice_id
            
            logger.error("No voices found in response")
            return None
            
        except Exception as e:
            logger.error(f"Error getting voices: {str(e)}")
            if 'response' in locals():
                logger.error(f"Response status code: {response.status_code}")
                logger.error(f"Response text: {response.text}")
            return None

    def _upload_video(self, video_path: str) -> Optional[str]:
        """
        Upload a video to Heygen using the correct endpoint
        """
        try:
            if not os.path.exists(video_path):
                raise ValueError(f"Video file not found: {video_path}")
                
            # Prepare headers with content type
            upload_headers = {
                "Content-Type": "video/mp4",
                "X-Api-Key": self.api_key
            }
                
            # Direct file upload
            with open(video_path, "rb") as f:
                response = requests.post(
                    self.upload_url,
                    data=f,
                    headers=upload_headers
                )
                response.raise_for_status()
                
                result = response.json()
                if 'data' in result and 'url' in result['data']:
                    return result['data']['url']
                else:
                    logger.error(f"Unexpected response format: {result}")
                    return None
                
        except Exception as e:
            logger.error(f"Error uploading video: {str(e)}")
            if 'response' in locals():
                logger.error(f"Response status code: {response.status_code}")
                logger.error(f"Response text: {response.text}")
            return None

    def _wait_for_completion(self, video_id: str, timeout: int = 900) -> Optional[Dict]:
        """
        Wait for video generation to complete using the v1 status check endpoint
        """
        try:
            start_time = time.time()
            last_status = None
            status_count = 0
            
            while time.time() - start_time < timeout:
                # Use the v1 endpoint for status checks
                response = requests.get(
                    "https://api.heygen.com/v1/video_status.get",
                    headers=self.headers,
                    params={"video_id": video_id}
                )
                response.raise_for_status()
                
                result = response.json()
                data = result.get('data', {})
                status = data.get('status')
                
                # Track status changes
                if status != last_status:
                    logger.info(f"Video status changed to: {status}")
                    last_status = status
                    status_count = 0
                else:
                    status_count += 1
                    if status_count % 10 == 0:  # Log every 10th check with the same status
                        logger.info(f"Video still {status}... (checked {status_count} times)")
                
                if status == 'completed':
                    logger.info("Video generation completed successfully")
                    # Download the video when completed
                    video_url = data.get('video_url')
                    if video_url:
                        downloaded_path = self._download_video(video_url, f"output/video_{video_id}.mp4")
                        if downloaded_path:
                            data['local_path'] = downloaded_path
                    return data
                elif status == 'failed':
                    error = data.get('error', {})
                    error_msg = error.get('message', 'Unknown error')
                    logger.error(f"Video generation failed: {error_msg}")
                    return None
                
                # Adaptive sleep time based on status
                if status == 'processing':
                    time.sleep(10)  # Check every 10 seconds when processing
                else:
                    time.sleep(5)   # Check every 5 seconds for other statuses
            
            # If we timeout, try one last time to get the status
            logger.warning(f"Timeout reached after {timeout} seconds. Checking final status...")
            try:
                response = requests.get(
                    "https://api.heygen.com/v1/video_status.get",
                    headers=self.headers,
                    params={"video_id": video_id}
                )
                response.raise_for_status()
                result = response.json()
                data = result.get('data', {})
                status = data.get('status')
                
                if status == 'completed':
                    logger.info("Video completed after timeout!")
                    video_url = data.get('video_url')
                    if video_url:
                        downloaded_path = self._download_video(video_url, f"output/video_{video_id}.mp4")
                        if downloaded_path:
                            data['local_path'] = downloaded_path
                    return data
                else:
                    logger.error(f"Video still in {status} state after timeout")
                    return None
                    
            except Exception as e:
                logger.error(f"Error checking final status: {str(e)}")
                return None
            
        except Exception as e:
            logger.error(f"Error checking video status: {str(e)}")
            if 'response' in locals():
                logger.error(f"Response status code: {response.status_code}")
                logger.error(f"Response text: {response.text}")
            return None

    def _download_video(self, video_url: str, save_path: str) -> Optional[str]:
        """
        Download a video from a URL and save it locally
        """
        try:
            logger.info(f"Downloading video from {video_url}")
            response = requests.get(video_url, stream=True)
            response.raise_for_status()
            
            # Create output directory if it doesn't exist
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            
            # Download the video
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            logger.info(f"Video downloaded successfully to {save_path}")
            return save_path
            
        except Exception as e:
            logger.error(f"Error downloading video: {str(e)}")
            return None

    def _truncate_text(self, text: str, max_words: int = 50) -> str:
        """
        Truncate text to a maximum number of words
        """
        words = text.split()
        if len(words) <= max_words:
            return text
        return ' '.join(words[:max_words]) + '...'

    def create_video(self, 
                    video_path: str, 
                    description: str,
                    avatar_url: Optional[str] = None,
                    max_retries: int = 3,
                    initial_timeout: int = 300) -> Optional[Dict]:
        """
        Create a video using Heygen API with the given stock video and description.
        If generation takes too long, will retry with shorter description.
        """
        current_description = description
        current_timeout = initial_timeout
        words_per_retry = 50  # Reduce by 50 words each retry
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempt {attempt + 1}/{max_retries} with {len(current_description.split())} words")
                
                # First, get available avatars and voices
                logger.info("Fetching available avatar...")
                avatar_id = self._get_first_available_avatar()
                if not avatar_id:
                    raise ValueError("Failed to get avatar ID")
                logger.info(f"Successfully got avatar ID: {avatar_id}")

                logger.info("Fetching available voice...")
                voice_id = self._get_first_available_voice()
                if not voice_id:
                    raise ValueError("Failed to get voice ID")
                logger.info(f"Successfully got voice ID: {voice_id}")
                
                # Upload the background video
                logger.info("Uploading background video...")
                video_url = self._upload_video(video_path)
                if not video_url:
                    raise ValueError("Failed to upload background video")
                logger.info(f"Successfully uploaded video. URL: {video_url}")
                
                # Create the video generation task
                logger.info("Preparing video generation payload...")
                payload = {
                    "video_inputs": [
                        {
                            "character": {
                                "type": "avatar",
                                "avatar_id": avatar_id,
                                "avatar_style": "normal"
                            },
                            "voice": {
                                "type": "text",
                                "input_text": current_description,
                                "voice_id": voice_id,
                                "speed": 1.0,
                                "volume": 1.0,
                                "pitch": 1.0,
                                "style": "normal"
                            },
                            "background": {
                                "type": "video",
                                "url": video_url,
                                "scale": "cover",
                                "play_style": "loop"
                            }
                        }
                    ],
                    "dimension": {
                        "width": 1280,
                        "height": 720
                    },
                    "test": True,
                    "caption": True
                }
                
                # Log the payload for debugging (excluding sensitive data)
                debug_payload = payload.copy()
                debug_payload['video_inputs'][0]['voice']['input_text'] = f"[{len(current_description)} chars]"
                logger.debug(f"Video generation payload: {debug_payload}")
                
                # Make the API request
                logger.info("Sending video generation request...")
                response = requests.post(
                    f"{self.base_url}/video/generate",
                    headers=self.headers,
                    json=payload
                )
                
                # Log the response status and headers
                logger.info(f"Response status code: {response.status_code}")
                logger.debug(f"Response headers: {dict(response.headers)}")
                
                # Try to parse the response
                try:
                    result = response.json()
                    logger.debug(f"Raw response body: {result}")
                except ValueError as e:
                    logger.error(f"Failed to parse response as JSON: {e}")
                    logger.error(f"Raw response content: {response.text}")
                    raise
                
                # Check for specific error conditions
                if response.status_code != 200:
                    error_msg = result.get('message', 'Unknown error')
                    error_code = result.get('code', 'No error code')
                    error_details = result.get('data', {})
                    error_info = result.get('error', {})
                    logger.error(f"API Error: {error_code} - {error_msg}")
                    logger.error(f"Error details: {error_details}")
                    logger.error(f"Error info: {error_info}")
                    logger.error(f"Full response: {result}")
                    raise ValueError(f"API Error: {error_info.get('message', error_msg)}")
                
                # Extract video ID
                video_id = result.get('data', {}).get('video_id')
                if not video_id:
                    logger.error("No video ID in response")
                    logger.error(f"Full response: {result}")
                    raise ValueError("No video ID in response")
                
                logger.info(f"Video generation task created with ID: {video_id}")
                
                # Wait for the video to be generated
                logger.info("Waiting for video generation to complete...")
                result = self._wait_for_completion(video_id, timeout=current_timeout)
                
                if result:
                    return result
                else:
                    # If we get here, the video generation timed out
                    if attempt < max_retries - 1:  # Don't truncate on the last attempt
                        # Truncate the description for the next attempt
                        current_description = self._truncate_text(current_description, 
                            max_words=len(current_description.split()) - words_per_retry)
                        logger.info(f"Generation timed out. Retrying with shorter description ({len(current_description.split())} words)")
                        current_timeout = max(180, current_timeout - 60)  # Reduce timeout but not below 3 minutes
                    else:
                        logger.error("All retry attempts failed")
                        return None
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Network error during video creation: {str(e)}")
                if hasattr(e, 'response') and e.response is not None:
                    logger.error(f"Response status code: {e.response.status_code}")
                    logger.error(f"Response text: {e.response.text}")
                if attempt < max_retries - 1:
                    continue
                raise
            except Exception as e:
                logger.error(f"Error in video creation: {str(e)}")
                if attempt < max_retries - 1:
                    continue
                raise 