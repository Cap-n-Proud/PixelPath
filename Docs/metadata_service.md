## Overview

The `MetadataService` module provides functionality to interact with media file metadata using the ExifTool library. It supports reading, writing, and modifying metadata such as creation times, GPS coordinates, ratings, and other IPTC fields.

---

## Class: MetadataService

### Initialization

```python
class MetadataService:
    def __init__(self, config)
```

**Parameters**
- `config`: Configuration object containing settings for the service (e.g., logging configuration).

The `MetadataService` initializes with a provided configuration and sets up logging using the `setup_logging` function from `log_service`.

---

### Methods

#### 1. `get_creation_time(file_path: Path) -> str`

**Description**
Extracts the creation datetime of a media file using ExifTool.

**Parameters**
- `file_path`: The path to the media file.

**Return Value**
A string representing the creation datetime in "YYYY:MM:DD HH:MM:SS" format, or `None` if not found.

**Example**

```python
metadata_service = MetadataService(config)
creation_time = await metadata_service.get_creation_time(file_path)
print(f"File created at: {creation_time}")
```

---

#### 2. `get_gps_coordinates(file_path: Path) -> Optional[Dict]`

**Description**
Extracts GPS coordinates (latitude and longitude) from a media file using ExifTool.

**Parameters**
- `file_path`: The path to the media file.

**Return Value**
A dictionary with keys `lat` and `lon`, or `None` if no GPS data is found.

**Example**

```python
metadata_service = MetadataService(config)
gps_data = await metadata_service.get_gps_coordinates(file_path)
if gps_data:
    print(f"GPS Coordinates: Lat={gps_data['lat']}, Lon={gps_data['lon']}")
```

---

#### 3. `write_metadata(file_path: Path, data: Dict[str, Any], media_type: str)`

**Description**
Writes metadata to a file using ExifTool, with behavior configurable via the `metadata_behavior` setting in the configuration (e.g., `overwrite`, `append`, `do_nothing`).

**Parameters**
- `file_path`: The path to the media file.
- `data`: A dictionary containing metadata fields and their values. Example keys include:
  - `"tags"`: List of tags/keywords.
  - `"colors"`: Color-related metadata.
  - `"faces"`: Face-related metadata.
  - `"description"`: Caption or description.
  - `"ocr"`: OCR text extracted from the file.
  - `"geotag"`: Geolocation data.
- `media_type`: The type of media (e.g., `"image"`).

**Return Value**
None.

**Behavior Modes**
1. **`overwrite`**: Replaces existing metadata with new values.
2. **`append`**: Adds new metadata without removing existing values.
3. **`do_nothing`**: Skips writing metadata if it already exists.

**Example**

```python
metadata_service = MetadataService(config)
data = {
    "tags": ["vacation", "summer"],
    "description": "A beautiful sunset over the mountains.",
    "geotag": {"lat": 40.7128, "lon": -74.0060}
}
await metadata_service.write_metadata(file_path, data, media_type="image")
```

---

#### 4. `set_rating(rating: int, fname: str)`

**Description**
Sets the rating of a file using ExifTool.

**Parameters**
- `rating`: An integer representing the rating (typically between 0 and 5).
- `fname`: The path to the media file.

**Return Value**
None.

**Example**

```python
metadata_service = MetadataService(config)
await metadata_service.set_rating(rating=4, fname=file_path)
print("Rating updated successfully.")
```

---

## Notes

1. **Dependency Injection**: The service requires a configuration object for initialization. Ensure the configuration includes logging settings and any other necessary parameters.

2. **Asynchronous Operations**: Methods like `get_creation_time`, `get_gps_coordinates`, and `write_metadata` are asynchronous and should be called with `await`.

3. **ExifTool Requirements**: This service relies on ExifTool being installed and accessible in the system path. Ensure ExifTool is properly installed before using this service.

4. **Security Considerations**:
    - The `set_rating` method uses `subprocess.run` with `shell=True`. Avoid passing untrusted input to prevent shell injection attacks.
    - Always validate and sanitize file paths before passing them to these methods.

5. **Deprecated Methods**: The `write_metadataOLD` method is deprecated and should not be used in new code. Use the primary `write_metadata` method instead.

---

## Usage Examples

### Example 1: Extracting Metadata

```python
from pathlib import Path

# Initialize the service with a configuration object
metadata_service = MetadataService(config)

# Get creation time
file_path = Path("example.jpg")
creation_time = await metadata_service.get_creation_time(file_path)
print(f"File created at: {creation_time}")

# Get GPS coordinates
gps_data = await metadata_service.get_gps_coordinates(file_path)
if gps_data:
    print(f"GPS Coordinates: Lat={gps_data['lat']}, Lon={gps_data['lon']}")
```

### Example 2: Writing Metadata

```python
metadata_service = MetadataService(config)

data = {
    "tags": ["vacation", "summer"],
    "description": "A beautiful sunset over the mountains.",
    "geotag": {"lat": 40.7128, "lon": -74.0060}
}

await metadata_service.write_metadata(file_path, data, media_type="image")
print("Metadata updated successfully.")
```

---

## Configuration

The `config` object should include at least the following parameters:

- **Logging Configuration**:
    ```python
    {
        "logging": {
            "level": "INFO",
            "file": "metadata_service.log"
        }
    }
    ```

---

This documentation provides a comprehensive guide to using the `MetadataService` class and its associated methods. For further assistance, refer to the source code or contact support.