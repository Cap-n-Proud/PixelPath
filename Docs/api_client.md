
---

# API Client User Manual

## Module Overview
The `APIClient` class provides an asynchronous HTTP client for interacting with external APIs. It handles POST and GET requests, processes responses, and includes logging functionality.

---

## Class: APIClient

### Purpose and Use Case
The `APIClient` is designed to interact with external web services via HTTP requests. It supports both POST and GET methods and includes error handling and logging capabilities.

### Initialization
```python
def __init__(self, config):
```

#### Parameters:
- `config`: Configuration object containing API URLs and processing parameters.
  - Example: `config.api` should contain attributes like `image_analysis_url`, `transcribe_url`, etc.

#### Key Notes:
1. The client uses the `httpx` library for asynchronous HTTP requests with a timeout of 30 seconds.
2. Logging is configured using `setup_logging(config)` and logs are captured via the root logger.

---

## Methods

### 1. `post_request`
```python
async def post_request(self, endpoint: str, payload: dict) -> Optional[dict]
```

#### Parameters:
- `endpoint`: URL of the API endpoint to send the POST request.
- `payload`: Dictionary containing the request body data.

#### Return Value:
- Returns a dictionary with the API response if successful.
- Returns `None` if the request fails or times out.

#### Error Handling:
- Logs errors using `self.logger.error()` and returns `None` on failure.

### 2. `get_request`
```python
async def get_request(self, endpoint: str, payload: dict) -> Optional[dict]
```

#### Parameters:
- Same as `post_request()`.
  
#### Return Value and Error Handling:
- Identical to `post_request()` but sends a GET request instead of POST.

### 3. `get_image_analysis`
```python
async def get_image_analysis(self, image_path: Path, service_type: str) -> Optional[dict]
```

#### Parameters:
- `image_path`: Path object pointing to the image file.
- `service_type`: String specifying the type of analysis (e.g., "image" or "video").

#### Return Value:
- Returns a dictionary with the analysis results if successful.
- Returns `None` on failure.

#### Key Notes:
1. The method constructs the URL dynamically using `getattr()` based on the `service_type`.
2. The payload includes:
   - `"image"`: Path to the image file as a string.
   - `"confidence"`: Confidence threshold from configuration.

### 4. `transcribe_audio`
```python
async def transcribe_audio(self, audio_path: Path) -> Optional[str]
```

#### Parameters:
- `audio_path`: Path object pointing to the audio file.

#### Return Value:
- Returns a string containing the transcription result if successful.
- Returns `None` on failure.

#### Key Notes:
1. The method sends an audio file to a transcription service.
2. Uses a fixed `"medium"` model for transcription (can be configurable in future).

---

## Example Usage

### Initialization
```python
from api_client import APIClient

# Configure your settings
class Config:
    class api:
        image_analysis_url = "https://api.example.com/image/analyze"
        transcribe_url = "https://api.example.com/audio/transcribe"
    
    class processing:
        obj_confidence = 0.75
        
config = Config()
client = APIClient(config)
```

### Image Analysis
```python
from pathlib import Path

# Analyze an image
image_path = Path("path/to/image.jpg")
result = await client.get_image_analysis(image_path, service_type="image")

if result:
    print(f"Analysis complete: {result}")
else:
    print("Failed to analyze image.")
```

### Audio Transcription
```python
audio_path = Path("path/to/audio.mp3")
transcription = await client.transcribe_audio(audio_path)

if transcription:
    print(f"Transcription: {transcription}")
else:
    print("Failed to transcribe audio.")
```

---

## Key Notes and Considerations

1. **Asynchronous Usage**:
   - All methods are asynchronous and must be called with `await`.
   - Ensure your environment supports async/await.

2. **Error Handling**:
   - Methods log errors using the root logger but do not raise exceptions.
   - Return `None` on failure, so always check results before processing.

3. **Logging Configuration**:
   - Logging is set up using `setup_logging(config)` in the constructor.
   - Modify logging levels and handlers in `log_service.py`.

4. **Configuration Requirements**:
   - Ensure your `config` object contains all required API URLs and parameters.

5. **Payload Construction**:
   - Methods construct payloads dynamically based on input parameters.
   - Verify that all required fields are provided by the configuration.

---
