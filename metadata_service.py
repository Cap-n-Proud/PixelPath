# metadata_service.py

# The `MetadataService` module provides functionality to interact with media file metadata using the ExifTool library. 
# It supports reading, writing, and modifying metadata such as creation times, GPS coordinates, ratings, and other IPTC fields.


import exiftool
from pathlib import Path
import logging
from typing import Dict, Any, Optional, List

import logging
from log_service import setup_logging
import subprocess
import json


class MetadataService:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        # Setup logging before using it
        setup_logging(config)  # Make sure logging is configured

        # Directly use the root logger
        self.logger = logging.getLogger()  # No need to use __name__ here

    async def get_creation_time(self, file_path: Path) -> str:
        """Get media creation datetime using exiftool"""
        with exiftool.ExifTool() as et:
            metadata = et.get_metadata(str(file_path))
            return metadata.get("EXIF:DateTimeOriginal") or metadata.get(
                "QuickTime:CreateDate"
            )

    async def get_gps_coordinates(self, file_path: Path) -> Optional[Dict]:
        """Extract GPS coordinates using exiftool via subprocess"""
        try:
            result = subprocess.run(
                ["exiftool", "-json", "-GPSLatitude", "-GPSLongitude", str(file_path)],
                capture_output=True,
                text=True,
                check=True,
            )
            metadata = json.loads(result.stdout)
            if not metadata or not isinstance(metadata, list):
                return None

            gps_data = metadata[0]
            lat = gps_data.get("GPSLatitude")
            lon = gps_data.get("GPSLongitude")

            if lat is None or lon is None:
                return None

            return {"lat": lat, "lon": lon}

        except Exception as e:
            print(f"Error extracting GPS: {e}")
            return None

    async def write_metadata(
        self, file_path: Path, data: Dict[str, Any], media_type: str
    ):
        """Write metadata to a file using exiftool, respecting configured behavior (overwrite, append, do_nothing)."""

        # Read existing metadata
        try:
            result = subprocess.run(
                ["exiftool", "-j", "-s3", str(file_path)],
                capture_output=True,
                text=True,
                check=True,
            )
            existing_metadata = json.loads(result.stdout)[0]
        except (subprocess.CalledProcessError, json.JSONDecodeError, IndexError):
            existing_metadata = {}

        command = ["exiftool", "-q", "-overwrite_original"]
        metadata_behavior = self.config.processing.metadata_behavior
        exif_args = []

        def handle_keywords(values: List[str]):
            """Handle keyword metadata updates based on behavior settings."""
            existing_keywords = (
                set(existing_metadata.get("Keywords", []))
                if "Keywords" in existing_metadata
                else set()
            )
            new_keywords = set(values)

            if metadata_behavior == "overwrite":
                return [
                    f"-IPTC:Keywords={v}" for v in new_keywords
                ]  # Replace all keywords

            if metadata_behavior == "append":
                keywords_to_add = new_keywords - existing_keywords  # Avoid duplicates
                return [f"-IPTC:Keywords+={v}" for v in keywords_to_add]

            return []  # do_nothing: No changes

        def handle_caption(value: str, label=""):
            """Handle caption updates based on behavior settings."""
            existing_caption = existing_metadata.get("Caption-Abstract", "")
            new_caption = f"\n{label}{value}" if label else value

            if metadata_behavior == "overwrite":
                return [f"-IPTC:Caption-Abstract={new_caption}"]

            if metadata_behavior == "append":
                if new_caption.strip() not in existing_caption:
                    return [
                        f"-IPTC:Caption-Abstract={existing_caption} {new_caption}".strip()
                    ]

            return []  # do_nothing

        # Process metadata fields
        for key, value in data.items():
            if not value:
                continue  # Skip empty values

            if key in {"tags", "colors", "faces"}:
                exif_args.extend(handle_keywords(value))

            elif key == "description":
                exif_args.extend(handle_caption(value))

            elif key == "ocr":
                exif_args.extend(handle_caption(value, label="OCR: "))

            elif key == "geotag":
                for geo_key, geo_value in value.items():
                    exif_args.append(f"-IPTC:Keywords+={geo_value}")

            else:
                existing_value = existing_metadata.get(key, "")
                if metadata_behavior == "overwrite":
                    exif_args.append(f"-IPTC:{key}={value}")
                elif metadata_behavior == "append" and value not in existing_value:
                    exif_args.append(f"-IPTC:{key}+={value}")

        # Execute exiftool command
        if exif_args:
            command.extend(exif_args)
            command.append(str(file_path))
            subprocess.run(command, check=True)
            self.logger.info("Metadata written for %s", file_path)

    async def write_metadataOLD(
        self, file_path: Path, data: Dict[str, Any], media_type: str
    ):
        """Write metadata to file using exiftool, considering existing metadata values based on configuration."""

        command = ["exiftool", "-j", "-s3", str(file_path)]
        existing_metadata = subprocess.run(
            command, capture_output=True, text=True, check=True
        ).stdout

        # Parse JSON output to dictionary
        try:
            existing_metadata = json.loads(existing_metadata)[0]
        except json.JSONDecodeError:
            existing_metadata = {}  # If JSON parsing fails, assume no existing metadata

        command = ["exiftool", "-q", "-overwrite_original"]
        exif_args = []

        # Use the configured behavior for metadata processing
        metadata_behavior = self.config.processing.metadata_behavior

        # Collect descriptions and OCR results
        captions = []
        for key, value in data.items():
            if media_type == "image":
                if key == "tags":
                    if "Keywords" in existing_metadata:
                        existing_keywords = existing_metadata["Keywords"]
                        for v in value:
                            if v in existing_keywords:
                                if metadata_behavior == "overwrite":
                                    exif_args.append(f"-IPTC:Keywords={v}")
                                # do_nothing would not add this value
                            else:
                                if metadata_behavior != "do_nothing":
                                    exif_args.append(f"-IPTC:Keywords-={v}")
                                    exif_args.append(f"-IPTC:Keywords+={v}")
                    else:
                        # No existing keywords, add all
                        for v in value:
                            exif_args.append(f"-IPTC:Keywords+={v}")
                elif key in ["colors", "faces"]:
                    # Assuming colors and faces are also handled as keywords
                    if "Keywords" in existing_metadata:
                        existing_keywords = existing_metadata["Keywords"]
                        for v in value:
                            if v in existing_keywords:
                                if metadata_behavior == "overwrite":
                                    exif_args.append(f"-IPTC:Keywords={v}")
                                # do_nothing would not add this value
                            else:
                                if metadata_behavior != "do_nothing":
                                    exif_args.append(f"-IPTC:Keywords-={v}")
                                    exif_args.append(f"-IPTC:Keywords+={v}")
                    else:
                        for v in value:
                            exif_args.append(f"-IPTC:Keywords+={v}")
                elif key == "description":
                    if "Caption-Abstract" in existing_metadata and len(value):
                        if metadata_behavior == "append":
                            captions.append(
                                existing_metadata["Caption-Abstract"] + " " + value
                            )
                        elif metadata_behavior == "overwrite":
                            captions = [value]
                        # do_nothing would just not append anything new
                    else:
                        captions.append(value)
                elif key == "ocr":
                    # Add a newline before OCR results
                    if "Caption-Abstract" in existing_metadata and len(value):
                        if metadata_behavior == "append":
                            captions.append("\nOCR: " + value)

                    else:
                        captions.append("\nOCR: " + value)
                elif key == "geotag":
                    # Add geotag values as keywords
                    for geo_key, geo_value in value.items():
                        if isinstance(geo_value, list):  # Handle lists in geotag
                            for v in geo_value:
                                exif_args.append(f"-IPTC:Keywords-={v}")
                                exif_args.append(f"-IPTC:Keywords+={v}")
                        else:
                            exif_args.append(f"-IPTC:Keywords+={geo_value}")
                else:
                    # For other tags, apply the default behavior which is append
                    if key in existing_metadata:
                        if value in existing_metadata[key]:
                            if metadata_behavior.get(key, "append") == "overwrite":
                                exif_args.append(f"-IPTC:{key}={value}")
                            # do_nothing would not write anything
                        else:
                            if metadata_behavior.get(key, "append") != "do_nothing":
                                exif_args.append(f"-IPTC:{key}+={value}")
                    else:
                        exif_args.append(f"-IPTC:{key}={value}")

        # Combine all captions into one, with OCR prefixed by a newline
        if captions:
            full_caption = " ".join(captions)
            exif_args.append(f"-IPTC:Caption-Abstract={full_caption}")

        command.extend(exif_args)
        command.append(str(file_path))  # Add the file path

        subprocess.run(command, check=True)
        self.logger.info("Metadata written for image %s", file_path)

    async def write_metadataOLD(
        self, file_path: Path, data: Dict[str, Any], media_type: str
    ):
        """Write metadata to file using exiftool with proper mappings, ensuring no duplication."""

        command = ["exiftool", "-q", "-overwrite_original"]
        exif_args = []

        # Collect descriptions and OCR results
        captions = []
        for key, value in data.items():
            if media_type == "image":
                if key in ["tags", "colors", "faces"]:
                    for v in value:
                        exif_args.append(f"-IPTC:Keywords+={v}")
                elif key == "description":
                    captions.append(value)
                elif key == "ocr":
                    # Add a newline before OCR results
                    captions.append("\nOCR: " + value)
                elif key == "geotag":
                    # Add geotag values as keywords
                    for geo_key, geo_value in value.items():
                        if isinstance(geo_value, list):  # Handle lists in geotag
                            for v in geo_value:
                                exif_args.append(f"-IPTC:Keywords+={v}")
                        else:
                            exif_args.append(f"-IPTC:Keywords+={geo_value}")
                else:
                    exif_args.append(f"-IPTC:{key}={value}")

        # Combine all captions into one, with OCR prefixed by a newline
        if captions:
            full_caption = " ".join(captions)
            exif_args.append(f"-IPTC:Caption-Abstract={full_caption}")

        command.extend(exif_args)
        command.append(str(file_path))  # Add the file path

        subprocess.run(command, check=True)
        self.logger.info("Metadata written for image %s", file_path)

    async def set_rating(self, rating, fname):
        # Construct the ExifTool command
        command = f"exiftool -overwrite_original -Rating={rating} '{fname}'"

        # Run the command
        subprocess.run(command, shell=True, check=True)
        self.logger.debug(f"|set_rating| Rating set to {rating} for {fname}")
