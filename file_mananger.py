# media_workflow/file_manager.py
import shutil
import os
from pathlib import Path
import logging
from typing import Set
from datetime import datetime  # Correct import for datetime
import cv2


class FileManager:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.processed_files: Set[str] = set()

    async def organize_file(self, file_path: Path, media_type: str) -> Path:
        """Move file to organized directory structure"""
        dest_dir = (
            self.config.paths.image_dest
            if media_type == "image"
            else self.config.paths.video_dest
        )

        creation_time = self._get_creation_time(file_path, media_type)
        new_path = dest_dir / f"{creation_time:%Y/%m}" / file_path.name

        new_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(file_path), str(new_path))
        self.logger.debug(f"Moved {file_path} to {new_path}")
        return new_path

    def _get_creation_time(self, file_path: Path, media_type: str) -> datetime:
        # Implementation using exiftool/ffprobe
        return datetime.now()

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

        # cv2.imwrite(
        #     str(os.path.dirname(os.path.abspath(image_path))) + "/out.jpg", img_resized
        # )
        # print(str(os.path.dirname(os.path.abspath(image_path))) + "/out.jpg")

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
