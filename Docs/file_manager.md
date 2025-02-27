
# FileManager Class User Manual

## Overview
The `FileManager` class provides functionalities for organizing, resizing, and managing files within a media workflow. It handles file organization based on creation/modification times, temporary directory management, and image resizing.

---

## Class: FileManager

### Initialization
```python
def __init__(self, config):
```

#### Parameters:
- `config`: A configuration object containing paths and settings.
  - Example: `config.paths` should include attributes like `image_dest`, `video_dest`, and `ramdisk_dir`.
  
#### Key Notes:
1. The logger is initialized for the class to record events.
2. `processed_files` keeps track of files that have been processed.

---

## Methods

### 1. `organize_file`
```python
async def organize_file(self, path: str) -> str
```

#### Parameters:
- `path`: Path to the file to be organized.

#### Functionality:
- Determines if the file is an image or video and extracts its creation time.
- Creates a destination directory based on the year and month of the file's creation/modification date.
- Moves the file to the new location only if it doesn't already exist there.

#### Key Notes:
1. Uses `exiftool` for images and `ffprobe` for videos to extract metadata.
2. Sets directory permissions recursively to `0o777`.
3. Logs actions using the class logger.

### 2. `organize_fileOLD`
```python
async def organize_fileOLD(self, file_path: Path, media_type: str) -> Path
```

#### Parameters:
- `file_path`: Path object of the file to be organized.
- `media_type`: String indicating whether it's an "image" or "video".

#### Functionality:
- Similar to `organize_file` but uses a different method for determining creation time and organizing files.

#### Key Notes:
1. This method is marked as outdated (`OLD`) in the codebase.
2. Directly calls `_get_creation_time`, which currently returns the current datetime.

### 3. `_get_creation_time`
```python
def _get_creation_time(self, file_path: Path, media_type: str) -> datetime
```

#### Parameters:
- `file_path`: Path to the file.
- `media_type`: Type of media ("image" or "video").

#### Return Value:
- Returns a `datetime` object representing the creation time.

#### Key Notes:
1. Currently returns the current datetime (`datetime.now()`) but is intended for future implementation with actual metadata extraction.

### 4. `create_temp_dir`
```python
def create_temp_dir(self, prefix: str) -> Path
```

#### Parameters:
- `prefix`: Prefix for the temporary directory name.

#### Return Value:
- Returns a Path object pointing to the newly created temporary directory.

#### Functionality:
- Creates a temporary directory on the ramdisk with the specified prefix.

#### Key Notes:
1. The directory is created with permissions that allow read/write/execute access (`0o777`).

### 5. `cleanup_temp_dir`
```python
def cleanup_temp_dir(self, path: Path)
```

#### Parameters:
- `path`: Path to the temporary directory to be cleaned up.

#### Functionality:
- Removes the specified temporary directory and its contents.

#### Key Notes:
1. Uses `shutil.rmtree` with `ignore_errors=True` to safely remove directories.
2. Logs the cleanup action using the class logger.

### 6. `resize_image`
```python
async def resize_image(self, path: Path, max_width: int = 1980) -> bytes
```

#### Parameters:
- `path`: Path to the image file to be resized.
- `max_width` (optional): Maximum width of the resized image in pixels.

#### Return Value:
- Returns a bytes object containing the resized image in JPEG format.

#### Functionality:
- Reads the image using OpenCV, resizes it while maintaining aspect ratio, and converts it to a JPEG byte stream with 90% quality.

#### Key Notes:
1. Uses `cv2.INTER_LANCZOS4` for high-quality image resizing.
2. Logs debug information about the resized image dimensions.

---

## Example Usage

### Initialization
```python
from file_manager import FileManager

# Configure your settings
class Config:
    class paths:
        image_dest = "/path/to/image/destination"
        video_dest = "/path/to/video/destination"
        ramdisk_dir = "/dev/shm"  # Common location for RAM disks
        
config = Config()
file_manager = FileManager(config)
```

### Organizing a File
```python
# Example with an image file
image_path = "path/to/image.jpg"
organized_path = await file_manager.organize_file(image_path)
print(f"Organized path: {organized_path}")

# Example with a video file
video_path = "path/to/video.mp4"
organized_video_path = await file_manager.organize_file(video_path)
print(f"Organized video path: {organized_video_path}")
```

### Creating and Cleaning Up Temp Directory
```python
temp_dir = file_manager.create_temp_dir("temp_data_")
print(f"Temporary directory created at: {temp_dir}")

# Cleanup after use
file_manager.cleanup_temp_dir(temp_dir)
print(f"Cleaned up temporary directory.")
```

### Resizing an Image
```python
image_path = "path/to/large_image.jpg"
resized_image_bytes = await file_manager.resize_image(Path(image_path), max_width=1024)

# Save resized image
with open("resized_image.jpg", "wb") as f:
    f.write(resized_image_bytes)
print("Image resized and saved.")
```

---

## Key Notes and Considerations

1. **Asynchronous Methods**:
   - `organize_file` and `resize_image` are asynchronous and must be called with `await`.
   
2. **External Tools Dependency**:
   - The code relies on `exiftool` for image metadata extraction and `ffprobe` for video metadata.
   - Ensure these tools are installed and accessible in the system's PATH.

3. **File Handling**:
   - Methods may overwrite files if they already exist, but checks are in place to prevent accidental overwrites.
   
4. **Performance Considerations**:
   - Resizing images can be CPU-intensive, especially for large files or high resolutions.
   - Temporary directories on ramdisks (`/dev/shm`) offer fast access but have limited space and are volatile.

5. **Security Notes**:
   - Setting directory permissions to `0o777` allows full read/write/execute access, which can be a security concern in multi-user environments.

6. **Error Handling**:
   - Methods log errors and warnings via the class logger but do not raise exceptions.
   - Always check the return values before processing further steps.

---