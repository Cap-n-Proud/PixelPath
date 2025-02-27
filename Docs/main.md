# Media Workflow User Manual

## Table of Contents
1. **Introduction**
2. **Image Processor Module**
   - Class Structure
   - Methods Overview
   - Configuration & Dependencies
3. **Logging Module**
   - Setup and Configuration
   - Log Handlers and Formatters
4. **Main Application**
   - Entry Point and Configuration
   - Running the Application
5. **Example Configurations**
6. **Notes and Best Practices**

---

## 1. Introduction

The Media Workflow system is designed to automate various image processing tasks, including tagging, OCR text extraction, face recognition, color analysis, geotagging, and metadata management. This user manual provides an in-depth guide to understanding and utilizing the core components of this workflow.

---

## 2. Image Processor Module

### Class Structure

The `ImageProcessor` class is central to handling image-related tasks. It initializes with several dependencies:

```python
def __init__(self, config, metadata: MetadataService, api: APIClient, file_manager: FileManager):
    ...
```

**Parameters:**
- **config**: Configuration object containing workflow settings.
- **metadata**: Instance of `MetadataService` for handling metadata operations.
- **api**: Instance of `APIClient` to interact with external services (e.g., Clarifai, OCR engines).
- **file_manager**: Instance of `FileManager` for file organization and management.

### Methods Overview

#### 1. `process(image_path: Path) -> Dict`
Orchestrates the entire image processing pipeline based on enabled workflow tasks in the configuration.

**Parameters:**
- **image_path**: Path to the input image file.

**Returns:**
- A dictionary containing results from various processing steps (e.g., tags, OCR text).

**Enabled Tasks:**
- Image Tagging
- Geotagging
- Description Generation
- Color Analysis
- Face Recognition
- OCR

#### 2. `_get_image_tags(image_path: Path) -> List[str]`
Generates tags for an image using the Clarifai API.

**Parameters:**
- **image_path**: Path to the input image file.

**Returns:**
- A list of generated tags.

#### 3. `_process_ocr(image_path: Path) -> List[str]`
Extracts text from an image using OCR (Optical Character Recognition).

**Parameters:**
- **image_path**: Path to the input image file.

**Returns:**
- A list of extracted text fragments.

#### 4. `_classify_faces(image_path: Path) -> List[str]`
Identifies and classifies faces in an image.

**Parameters:**
- **image_path**: Path to the input image file.

**Returns:**
- A list of face classifications (e.g., names or labels).

#### 5. `_process_analyze_colors(image_path: Path) -> List[str]`
Analyzes and identifies dominant colors in an image.

**Parameters:**
- **image_path**: Path to the input image file.

**Returns:**
- A list of color names representing dominant colors.

### Configuration & Dependencies

Ensure your configuration includes:
```python
class AppConfig:
    def __init__(self):
        self.api = ApiConfig()
        self.paths = PathsConfig()
        self.processing = ProcessingConfig()
        self.workflow = WorkflowConfig()
        self.logging = LoggingConfig()
```

**Key Configurations:**
- **ApiConfig**: Contains URLs and keys for external services.
- **PathsConfig**: Specifies directories for logs, processed files, and temporary storage.
- **WorkflowConfig**: Enables/disables specific processing tasks.

---

## 3. Logging Module

The `logging.py` module simplifies logging configuration across the application.

### Setup and Configuration

```python
def setup_logging(config: AppConfig):
    ...
```

**Parameters:**
- **config**: Contains logging settings like log level and directory.

**Steps:**
1. Configures the root logger with the specified log level.
2. Removes any existing handlers to prevent duplication.
3. Adds two handlers:
   - **File Handler**: Logs messages to `media_workflow.log`.
   - **Stream Handler**: Prints logs to the console.

### Log Handlers and Formatters

- **Formatter**:
  ```plaintext
  [asctime][logger name][log level] message
  ```
  Example:
  ```plaintext
  [2023-10-20 14:30:45,678][root][INFO] Application started.
  ```

- **Module-Specific Log Levels**:
  - `httpx`: Set to WARNING to reduce HTTP client noise.
  - `ppocr`: Set to WARNING to minimize OCR-related logs.

---

## 4. Main Application

### Entry Point and Configuration

```python
async def main():
    controller = MediaController(config)
    await controller.start()
```

**Parameters:**
- **config**: Comprehensive application configuration.

**Configuration Example**:
```python
config = AppConfig(
    api=ApiConfig(
        caption_url="http://192.168.1.121:9111/predictions",
        ocr_url="http://192.168.1.121:9011/predict",
        rating_url="http://192.168.1.121:9997/predictions",
        # ... other API configurations
    ),
    paths=PathConfig(
        watch_dir=Path("/mnt/Photos/000-InstantUpload/"),
        image_dest=Path("/mnt/Photos/005-PhotoBook/"),
        video_dest=Path("/mnt/Photos/010-Videos/"),
        # ... other path configurations
    ),
    workflow=WorkflowConfig(
        images=ImageWorkflowConfig(
            enable_geotagging=True,
            enable_face_recognition=True,
            # ... other image workflow settings
        ),
        videos=VideoWorkflowConfig(
            move_processed_media=False,
        ),
    ),
)
```

### Running the Application

```bash
# Navigate to project directory
cd /mnt/Software/200-Apps/media_workflow/

# Activate virtual environment (if applicable)
source venv/bin/activate

# Run the application
python main.py
```

---

## 5. Example Configurations

**Example Configuration for Image Processing**:
```python
config.workflow.images = ImageWorkflowConfig(
    enable_geotagging=True,
    enable_face_recognition=True,
    enable_color_analysis=True,
    write_metadata=True,
    move_processed_media=True,
)
```

**Environment Variables**:
Ensure the following are set in your environment:
```bash
export CLARIFAI_API_KEY="your-api-key"
export CLARIFAI_APP_ID="your-app-id"
export REVERSE_GEO_API_KEY="your-geo-key"
export REPLICATE_API_TOKEN="your-replicate-token"
```

---

## 6. Notes and Best Practices

1. **Configuration Management**:
   - Keep your configuration file organized.
   - Regularly update API keys and paths as needed.

2. **Logging**:
   - Monitor logs for errors and performance insights.
   - Adjust log levels to control verbosity.

3. **Performance Considerations**:
   - Ensure sufficient disk space for logs and processed files.
   - Test with smaller datasets before full deployment.

4. **Security**:
   - Store sensitive information (e.g., API keys) securely using environment variables or encrypted configurations.

---

This manual provides a comprehensive guide to setting up and running the Media Workflow application, ensuring smooth operation and effective image processing. For further assistance or customization, refer to the code comments and documentation within each module.