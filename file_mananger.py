import shutil
import os
from pathlib import Path
import logging
from typing import Set
from datetime import datetime  # Correct import for datetime
import cv2
import subprocess
import json
from typing import Set, Optional


class FileManager:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.processed_files: set[str] = set()
        # setup_logging(config)  # Ensure logging is configured

    async def organize_file(
        self,
        path: str | Path,
        conflict_resolution: str = "skip",
        rename_suffix: str = "_{counter}",
    ) -> str:
        """
        Organize a file into the destination directory based on its creation/modification time.

        Args:
            path (str | Path): Path to the file to organize.
            conflict_resolution (str, optional):
                Strategy for handling file name conflicts at destination.
                Options: 'skip' (default), 'overwrite', 'rename'.
            rename_suffix (str, optional):
                Suffix to append when renaming files. Defaults to "_{counter}".

        Returns:
            str: The final path of the organized file or an error message.

        Raises:
            ValueError: If an invalid conflict_resolution strategy is provided.
        """
        if isinstance(path, str):
            path = Path(path)

        base_dest = self.config.paths.image_dest
        destination_folder, file_name = await self._get_destination_info(
            path, base_dest
        )

        # Create destination folder
        os.makedirs(destination_folder, exist_ok=True)
        self._set_directory_permissions(destination_folder)

        # Handle file name conflicts based on strategy
        final_path = Path(destination_folder) / file_name

        if not final_path.exists():
            self.logger.info(f"Moving '{path}' to '{final_path}'")
            shutil.move(str(path), str(final_path))
            return str(final_path)
        else:
            match conflict_resolution:
                case "skip":
                    self.logger.warning(
                        f"Skipping file '{path}'. File already exists at '{final_path}'."
                    )
                    return f"File not moved: Destination {final_path} already exists."
                case "overwrite":
                    self.logger.info(f"Overwriting existing file at '{final_path}'")
                    shutil.move(str(path), str(final_path))
                    return str(final_path)
                case "rename":
                    new_name = await self._handle_rename(
                        final_path, suffix=rename_suffix
                    )
                    if new_name:
                        self.logger.info(
                            f"Renaming '{path}' to '{new_name}' and moving."
                        )
                        shutil.move(str(path), str(new_name))
                        return str(new_name)
                    else:
                        error_msg = (
                            f"Failed to find a unique name for '{path}'. "
                            "File not moved."
                        )
                        self.logger.error(error_msg)
                        return error_msg
                case _:
                    raise ValueError(
                        f"Invalid conflict_resolution strategy: {conflict_resolution}"
                    )

    async def _get_destination_info(
        self, path: Path, base_dest: str
    ) -> tuple[str, str]:
        """Determine the destination folder and filename based on file creation/modification time."""
        if not os.path.exists(path):
            raise FileNotFoundError(f"File '{path}' does not exist.")

        # Determine file type-specific metadata
        suffix = (
            path.suffix.lower()
        )  # Get the extension as a string and convert to lowercase

        if suffix in self.config.image_extensions:
            metadata = await self._get_image_metadata(str(path))
            created_time = metadata.get("DateTimeOriginal", None)
        elif suffix in self.config.video_extensions:
            metadata = await self._get_video_metadata(str(path))
            created_time = metadata.get("creation_time", None)
        else:
            created_time = os.path.getctime(path)

        # Handle creation time
        if isinstance(created_time, float):
            timestamp_str = datetime.fromtimestamp(created_time).strftime(
                "%Y:%m:%d %H:%M:%S"
            )
        elif created_time and isinstance(created_time, str):
            timestamp_str = created_time.split(".")[0]
        else:
            timestamp_str = datetime.now().strftime("%Y:%m:%d %H:%M:%S")

        # Format the creation time to a usable datetime object
        file_date = await self._parse_timestamp(timestamp_str)

        destination_folder = os.path.join(
            base_dest, str(file_date.year), f"{file_date.month:02d}"
        )

        return destination_folder, path.name

    async def _set_directory_permissions(self, directory_path: str) -> None:
        """Set appropriate permissions for the target directory."""
        # Ensure directory exists
        os.makedirs(directory_path, exist_ok=True)
        # Set read/write/execute for everyone
        os.chmod(directory_path, 0o777)

    async def _get_image_metadata(self, path: str) -> dict:
        """Extract metadata using exiftool for images."""
        try:
            result = subprocess.run(
                ["exiftool", "-json", path],
                capture_output=True,
                text=True,
                check=True,
            )
            return json.loads(result.stdout)[0]
        except Exception as e:
            self.logger.error(f"Error extracting image metadata: {e}")
            raise

    async def _get_video_metadata(self, path: str) -> dict:
        """Extract metadata using ffprobe for videos."""
        try:
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "quiet",
                    "-print_format",
                    "json",
                    "-show_format",
                    "-show_streams",
                    path,
                ],
                capture_output=True,
                text=True,
                check=True,
            )
            return json.loads(result.stdout)
        except Exception as e:
            self.logger.error(f"Error extracting video metadata: {e}")
            raise

    async def _parse_timestamp(self, timestamp_str: str) -> datetime:
        """Convert a timestamp string to a datetime object."""
        for format_str in ["%Y:%m:%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"]:
            try:
                return datetime.strptime(timestamp_str.strip(), format_str)
            except ValueError:
                pass
        # If no valid format matches, use current time as fallback
        self.logger.warning(
            f"Failed to parse timestamp '{timestamp_str}'. Using current time."
        )
        return datetime.now()

    async def _handle_rename(
        self, existing_path: Path, suffix: str = "_{counter}"
    ) -> Optional[Path]:
        """
        Handle file renaming when a file already exists at the destination.

        Args:
            existing_path (Path): The path that already exists.
            suffix (str, optional): Suffix to append to create a unique name. Defaults to "_{counter}".

        Returns:
            Path | None: The new unique path if successfully renamed, otherwise None.
        """
        base_name = existing_path.stem
        extension = existing_path.suffix

        counter = 1
        while True:
            # Generate candidate name with suffix
            candidate_stem = base_name + suffix.format(counter=counter)
            candidate_path = existing_path.parent / f"{candidate_stem}{extension}"

            if not candidate_path.exists():
                return candidate_path
            else:
                counter += 1

            # Prevent infinite loops by limiting attempts (optional)
            if counter > 100:
                self.logger.error(
                    f"Failed to find a unique name for '{existing_path}'."
                )
                return None

    def create_temp_dir(self, prefix: str) -> Path:
        temp_dir = self.config.paths.ramdisk_dir / prefix
        temp_dir.mkdir(exist_ok=True)
        return temp_dir

    def cleanup_temp_dir(self, path: Path):
        shutil.rmtree(path, ignore_errors=True)
        self.logger.debug(f"Cleaned up temp directory: {path}")

    async def resize_image(self, path: Path, max_width=1980):
        """
        Resizes an image to a specified high resolution.

        :param path: The path to the input image.
        :param max_width: The desired high resolution size in pixels, as a tuple of (width, height).
        :return: The resized image as a bytes object.
        """
        # Load the image and resize it to the high resolution
        img = cv2.imread(path, cv2.IMREAD_UNCHANGED)

        # Get the original width and height of the image
        # Compute the aspect ratio of the original image
        orig_height, orig_width = img.shape[:2]
        aspect_ratio = orig_width / orig_height
        target_width = max_width
        target_height = int(target_width / aspect_ratio)
        # Resize the image using OpenCV
        img_resized = cv2.resize(
            img, (target_width, target_height), interpolation=cv2.INTER_LANCZOS4
        )
        resized_height, resized_width = img_resized.shape[:2]

        # Encode the resized image as a JPEG bytes object
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]
        _, img_bytes = cv2.imencode(".jpg", img_resized, encode_param)
        self.logger.debug(
            "|Tag Image| Image resized: "
            + str(path)
            + " "
            + str(resized_height)
            + " x "
            + str(resized_width)
        )

        return img_bytes.tobytes()
