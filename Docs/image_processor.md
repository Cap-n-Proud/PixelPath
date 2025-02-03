Here's the user manual in Markdown syntax:

```markdown
# Image Processor User Manual

## Overview

The `ImageProcessor` module is responsible for handling various image-processing tasks, including:

- **Image Tagging** (via Clarifai API)
- **AI Caption Generation**
- **OCR Processing** (via PaddleOCR)
- **Object Detection**
- **Face Recognition & Classification**
- **Color Analysis**
- **GPS Reverse Geocoding**
- **Metadata Writing** (via ExifTool)

This module is designed to work asynchronously and integrates with multiple services to extract useful metadata from images.

---

## Installation & Dependencies

Before using this module, ensure the following dependencies are installed:

```bash
pip install numpy face_recognition pillow scikit-learn pickle-mixin paddleocr requests
```

Also, ensure external services such as **Clarifai API**, **Replicate AI**, and **Reverse Geocoding API** have valid API keys set in the configuration.

---

## Configuration

The `ImageProcessor` relies on a structured configuration file. Relevant settings include:

```yaml
workflow:
  images:
    enable_tagging: true
    enable_geotagging: true
    enable_description: true
    enable_color_analysis: true
    enable_face_recognition: true
    enable_ocr: true
    write_metadata: true
    move_processed_media: true

api:
  CLARIFAI_API_KEY: "your_clarifai_api_key"
  REVERSE_GEO_API_KEY: "your_reverse_geo_api_key"
  caption_url: "https://api.example.com/caption"
```

---

## Usage

### Initializing the `ImageProcessor`

To use this module, initialize an instance of `ImageProcessor` with the required dependencies:

```python
from metadata_service import MetadataService
from api_client import APIClient
from file_manager import FileManager

config = load_config()  # Load your configuration
metadata = MetadataService(config)
api = APIClient(config)
file_manager = FileManager(config)

image_processor = ImageProcessor(config, metadata, api, file_manager)
```

### Processing an Image

To process an image, call:

```python
import asyncio
from pathlib import Path

image_path = Path("example.jpg")
results = asyncio.run(image_processor.process(image_path))

print(results)
```

The `process()` method will:

1. Extract metadata and GPS info (if enabled).
2. Generate tags, captions, and descriptions.
3. Perform OCR to detect text in images.
4. Identify and classify faces.
5. Analyze dominant colors.
6. Write metadata back to the image.
7. Move the processed image to a structured location (if enabled).

---

## Features & API Details

### Image Tagging

**Method:** `async def _get_image_tags(self, image_path: Path) -> List[str]`

- Uses the **Clarifai API** to generate image tags.
- Requires `CLARIFAI_API_KEY` in the configuration.

### AI Caption Generation

**Method:** `async def _generate_caption(self, image_path: Path) -> Optional[str]`

- Uses an AI-based caption generation model.
- Requires an external API (`caption_url`).

### OCR Processing

**Method:** `async def _process_ocr(self, image_path: Path) -> List[str]`

- Uses **PaddleOCR** to extract text from images.
- Returns detected text as a list of words.
- Confidence filtering is applied.

### Face Recognition & Classification

**Method:** `async def _classify_faces(self, image_path: Path) -> List[str]`

- Detects and classifies faces using **face_recognition** and **scikit-learn SVM**.
- If no trained classifier exists, a new model is trained.

### Color Analysis

**Method:** `async def _process_analyze_colors(self, image_path: Path) -> List[str]`

- Uses **K-Means clustering** to detect dominant colors.
- Maps detected colors to human-readable names.

### GPS Reverse Geocoding

**Method:** `async def _process_geotagging(self, image_path: Path) -> Dict`

- Extracts GPS coordinates from image metadata.
- Queries an external geocoding API to retrieve location data.

### Metadata Writing

**Method:** `async def write_metadata(self, image_path: Path, metadata: Dict, media_type: str)`

- Uses **ExifTool** to write extracted metadata back to the image.

---

## Logging & Debugging

- Logging is configured via `setup_logging(config)`.
- Use `self.logger.debug()` for detailed debug information.
- Logs can be found in the configured log directory.

---

## Troubleshooting

1. **Clarifai API errors**
   - Ensure `CLARIFAI_API_KEY` is correct.
   - Check if the API service is active.

2. **OCR not detecting text**
   - Increase `ocr_confidence` threshold in config.
   - Ensure PaddleOCR is correctly installed.

3. **Face recognition issues**
   - If classifier is missing, it will be retrained.
   - Ensure training images are properly labeled.

4. **Geolocation errors**
   - Check if GPS data is present in the image.
   - Ensure `REVERSE_GEO_API_KEY` is valid.

---

## Future Improvements

- **Object detection**: Integration with Detic for advanced object recognition.
- **Better AI captions**: Improve caption generation using multimodal AI models.
- **Cloud integration**: Support for cloud storage and remote processing.

---

## Conclusion

This module provides an automated pipeline for extracting useful insights from images. By leveraging AI, OCR, and metadata processing, it enhances image classification, tagging, and organization in a structured workflow.
```

This should provide a comprehensive guide for maintaining and extending the module. Let me know if you need any adjustments! 🚀