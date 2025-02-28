# Media Controller Manual

This manual provides an overview of the `media_controller.py` file, detailing its classes, methods, and functionality. It is designed for both intermediate and advanced users to understand how the controller manages media processing tasks.

## Class Overview

### `MediaController`

The `MediaController` class serves as the central orchestrator for managing media files and coordinating their processing through various services and processors.

#### Initialization (`__init__`)

- **Parameters**:
  - `config: AppConfig`: Configuration settings for the application, including paths, API details, and processing parameters.
  
- **Setup**:
  - Configures logging using `setup_logging`.
  - Initializes dependencies such as `FileManager`, `MetadataService`, `APIClient`, and `ImageProcessor`.
  - Sets up a `TaskRunner` to manage concurrent tasks.

#### Methods

1. **`start()`**
   - **Purpose**: Initiates the media processing workflow.
   - **Functionality**:
     - Logs the start of the process.
     - Runs `_watch_directory()` and `task_runner.run()` concurrently using `asyncio.gather()`.
   
2. **`_watch_directory()`**
   - **Purpose**: Continuously monitors a specified directory for new files.
   - **Functionality**:
     - Scans the input directory (recursively if configured) for files older than a specified minimum age (`min_file_age`).
     - Collects and returns a list of paths to new files.

3. **`_find_new_files()`**
   - **Purpose**: Identifies new files in the watch directory based on file age.
   - **Functionality**:
     - Checks each file's modification time against `time.time()`.
     - Returns sorted paths of files that meet the criteria (older than `min_file_age` and not previously processed).

4. **`_process_file(file_path: Path)`**
   - **Purpose**: Handles individual media files for processing.
   - **Functionality**:
     - Determines the media type (image or video) based on file extension.
     - Adds the file to the `TaskRunner` queue for processing.

5. **`_process_media(file_path: Path, media_type: str)`**
   - **Purpose**: Processes a single media file.
   - **Functionality**:
     - If simulation is enabled (`simulate_processing`), logs the action without actual processing.
     - For images, delegates processing to `ImageProcessor`.
     - Adds processed files to a set of tracked files to prevent reprocessing.

## Key Features and Notes

### Configuration Parameters
- **Watch Interval**: The time between directory scans (`watch_interval`).
- **Minimum File Age**: Ensures files are sufficiently old before processing (`min_file_age`).
- **Recursive Search**: Configures whether to scan subdirectories recursively.
- **Simulation Mode**: Temporarily disables actual processing for testing.

### Important Considerations
- **File Tracking**: Uses a set to track processed files, preventing reprocessing of the same file.
- **Concurrency Management**: Utilizes `TaskRunner` to control the number of concurrent tasks (`max_concurrent`).

## Usage

To use the `MediaController`, instantiate it with an appropriate `AppConfig` and call the `start()` method.

```python
from media_controller import MediaController
import asyncio

# Example configuration setup (assuming AppConfig is properly configured)
config = AppConfig(
    # ... your configuration details ...
)

async def main():
    controller = MediaController(config)
    await controller.start()

asyncio.run(main())
```

## Notes for Advanced Users

1. **Customization**:
   - Modify the `TaskRunner` parameters to adjust concurrency levels.
   - Implement additional media types by extending the `_process_media` method.

2. **Logging**:
   - Use the logger instance (`self.logger`) to track workflow progress and debug issues.

3. **Extensibility**:
   - Add new processors (e.g., for video files) by integrating them into the controller.
   - Extend file tracking mechanisms if needed beyond the current set-based approach.

## Conclusion

The `MediaController` is a robust component designed to manage media processing workflows efficiently. By leveraging asynchronous operations and dependency injection, it provides flexibility and scalability for different use cases.