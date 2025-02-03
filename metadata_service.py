# media_workflow/metadata_service.py
import exiftool
from pathlib import Path
import logging
from typing import Dict, Any, Optional

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
        """Extract GPS coordinates from metadata"""

        with exiftool.ExifToolHelper() as et:
            metadata = et.get_metadata(file_path)
        # Ensure there's at least one dictionary in the metadata
        if not metadata:
            return None

        metadata = metadata[0]
        lat = 0
        lon = 0
        # Check if GPS data exists
        lat = metadata.get("EXIF:GPSLatitude")
        lon = metadata.get("EXIF:GPSLongitude")

        if lat is None or lon is None:
            return None
        self.logger.debug(f"Extracted GPS coordinates for {file_path}: {lat}, {lon}")
        return {"lat": lat, "lon": lon}

    async def write_metadata(
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
