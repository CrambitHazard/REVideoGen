# Real Estate Video Pipeline

An AI-powered pipeline that automatically creates professional real estate videos by combining stock footage with AI-generated descriptions and Heygen's video generation capabilities.

## Features

- Automatic stock video search and download using Pexels API
- AI-generated room descriptions using DistilGPT-2
- Professional video generation with voiceover using Heygen
- Modular and extensible pipeline architecture
- Comprehensive error handling and logging

## Prerequisites

- Python 3.8+
- Pexels API key
- Heygen API key

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/real-estate-video-pipeline.git
cd real-estate-video-pipeline
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the root directory with your API keys:
```
PEXELS_API_KEY=your_pexels_api_key
HEYGEN_API_KEY=your_heygen_api_key
```

## Usage

1. The pipeline can be run using the main script:

```bash
python main.py
```

2. To customize the rooms and features, modify the `rooms` list in `main.py`:

```python
rooms = [
    {
        'type': 'living room',
        'features': ['spacious', 'modern', 'natural light']
    },
    {
        'type': 'garden terrace',
        'features': ['private', 'landscaped', 'outdoor seating']
    }
]
```

## Project Structure

- `video_scraper.py`: Handles stock video search and download
- `gpt_description.py`: Generates room descriptions using DistilGPT-2
- `heygen_integration.py`: Manages video generation with Heygen
- `main.py`: Pipeline orchestrator
- `downloads/`: Directory for downloaded stock videos
- `output/`: Directory for final generated videos

## Error Handling

The pipeline includes comprehensive error handling:
- Failed video downloads
- API errors
- Video generation failures
- Missing API keys

All errors are logged with detailed information for debugging.

## Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 