## 1. Introduction

The `logging.py` file provides utilities for setting up logging in your application. It simplifies the process of configuring both file and console logging based on a provided configuration object.

**Purpose:**
- Configure root logger with specified settings.
- Set log levels for different modules to control verbosity.
- Format logs consistently for better readability.

---

## 2. Key Functions

### `setup_logging(config: AppConfig)`
Initializes the logging system using the provided configuration.

#### Parameters:
- **config**: An instance of `AppConfig` containing logging configurations such as:
  - `logging.level`: Sets the log level (e.g., DEBUG, INFO, WARNING).
  - `paths.log_dir`: Specifies the directory for storing log files.

**What It Does:**
1. Configures the root logger with the specified log level.
2. Removes any existing handlers to prevent duplicate logs.
3. Adds two handlers:
   - **File Handler**: Logs messages to a file named `media_workflow.log` in the specified directory.
   - **Stream Handler**: Prints logs to the console.
4. Both handlers use the same formatter for consistent output.

---

## 3. Logging Setup

### Logger Configuration
- The root logger is set to the level specified in your configuration (e.g., INFO).
- Two handlers are added:
  - **File Handler**:
    - Logs messages to `media_workflow.log`.
    - Path: Specified by `config.paths.log_dir`.
  - **Stream Handler**:
    - Prints logs directly to the console.
  
### Formatter
The formatter ensures that all log messages follow a consistent format:

```plaintext
[asctime][logger name][log level] message
```

For example:

```plaintext
[2023-10-20 14:30:45,678][root][INFO] Logging setup complete.
```

### Module-Specific Log Levels
The script adjusts the logging levels for specific modules to reduce noise:
- `httpx`: Set to WARNING to suppress unnecessary messages from HTTP client requests.
- `ppocr`: Set to WARNING to minimize verbose logs from OCR operations.

---

## 4. Notes

1. **Configuration Requirements**:
   - Ensure your `AppConfig` includes the necessary logging settings:
     ```python
     class AppConfig:
         def __init__(self):
             self.logging = LoggingConfig()
             self.paths = PathsConfig()

     class LoggingConfig:
         level: str = "INFO"  # Possible values: DEBUG, INFO, WARNING, ERROR, CRITICAL

     class PathsConfig:
         log_dir: Path = Path("logs")  # Directory for storing logs
     ```

2. **Log File Management**:
   - Logs are stored in `media_workflow.log` within the specified directory.
   - Ensure the log directory exists and has write permissions.

3. **Verbosity Control**:
   - Adjusting module-specific log levels (e.g., `httpx`) helps reduce noise from external libraries.

4. **Log Rotation**:
   - Manual file rotation or cleanup is required if logs grow too large.
   - Consider using a logging library like `rotating_filehandler` for automatic log rotation.

---

## 5. Example Usage

### Step 1: Define Configuration
```python
from config import AppConfig

# Create configuration object
config = AppConfig()
config.logging.level = "INFO"
config.paths.log_dir = Path("logs")
```

### Step 2: Set Up Logging
```python
import logging
from media_workflow.utils import setup_logging

setup_logging(config)
logger = logging.getLogger()

# Test logging
logger.info("Application started.")
logger.debug("This is a debug message.")
logger.warning("This is a warning.")
```

### Step 3: Output
You should see output in both the console and `logs/media_workflow.log`:
```plaintext
[2023-10-20 14:30:45,678][root][INFO] Application started.
[2023-10-20 14:30:45,679][root][DEBUG] This is a debug message.
[2023-10-20 14:30:45,680][root][WARNING] This is a warning.
```

---

## Conclusion

The `logging.py` module simplifies logging configuration in your application. By setting up both file and console handlers with a consistent format, it ensures that your logs are informative and easy to manage. Adjusting module-specific log levels helps control the verbosity of external libraries, making your logs more actionable.

For further customization, you can modify the formatter or add additional handlers (e.g., email notifications) as needed.