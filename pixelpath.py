import argparse
import asyncio
import json
import os
from pathlib import Path
from dataclasses import asdict
from dotenv import load_dotenv

from config import (
    AppConfig,
    ApiConfig,
    PathConfig,
    ProcessingConfig,
    WorkflowConfig,
    LoggingConfig,
    ImageWorkflowConfig,
    VideoWorkflowConfig,
    GeneralWorkflowConfig,
)
from media_controller import MediaController
from file_mananger import FileManager
from task_runner import TaskRunner
from metadata_service import MetadataService
from api_client import APIClient

# Load environment variables
load_dotenv()
CLARIFAI_API_KEY = os.getenv("CLARIFAI_API_KEY")
CLARIFAI_APP_ID = os.getenv("CLARIFAI_APP_ID")
REVERSE_GEO_API_KEY = os.getenv("REVERSE_GEO_API_KEY")
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")


def parse_args():
    parser = argparse.ArgumentParser(description="Media Workflow Processor")

    # Path-related arguments
    parser.add_argument(
        "--watch-dir", type=str, help="Directory to watch for new media files"
    )
    parser.add_argument(
        "--image-dest", type=str, help="Destination directory for processed images"
    )
    parser.add_argument(
        "--video-dest", type=str, help="Destination directory for processed videos"
    )

    # Workflow toggle arguments
    parser.add_argument(
        "--enable-geotagging", action="store_true", help="Enable image geotagging"
    )
    parser.add_argument(
        "--disable-geotagging", action="store_true", help="Disable image geotagging"
    )
    parser.add_argument(
        "--simulate",
        action="store_true",
        help="Run in simulation mode (no real processing)",
    )

    return parser.parse_args()


async def main():
    args = parse_args()

    # Load default config
    config = AppConfig(
        api=ApiConfig(
            caption_url="http://192.168.1.121:9111/predictions",
            ocr_url="http://192.168.1.121:9011/predict",
            rating_url="http://192.168.1.121:9997/predictions",
            obj_detection_url="http://192.168.1.121:9998/predictions",
            clarifai_url="https://clarify.com",
            wisper_url="http://192.168.1.121:9996/predictions",
            reverse_geo_url="https://api.opencagedata.com/geocode/v1/json?q=",
            REVERSE_GEO_API_KEY=REVERSE_GEO_API_KEY,
            face_detection_url="http://example.com/face",
            CLARIFAI_API_KEY=CLARIFAI_API_KEY,
            CLARIFAI_APP_ID=CLARIFAI_APP_ID,
            image_server_url="http://192.168.1.121:9999",
        ),
        paths=PathConfig(
            watch_dir=(
                Path(args.watch_dir)
                if args.watch_dir
                else Path("/mnt/Photos/000-InstantUpload/")
            ),
            image_dest=(
                Path(args.image_dest)
                if args.image_dest
                else Path("/mnt/Photos/005-PhotoBook/")
            ),
            video_dest=(
                Path(args.video_dest)
                if args.video_dest
                else Path("/mnt/Photos/010-Videos/")
            ),
            ramdisk_dir=Path("/ramdisk"),
            log_dir=Path("/mnt/Photos/001-Process/"),
            face_classifier=Path(
                "/mnt/Apps_Config/media_workflow/models/face_classifier.dat"
            ),
            known_faces_dir=Path("/mnt/Photos/990-Faces/known_faces"),
            unknown_faces_dir=Path("/mnt/Photos/990-Faces/unknown_faces"),
            temp_dir=Path("/tmp"),
            secrets_path=Path("/mnt/secrets/media_workflow/"),
        ),
        processing=ProcessingConfig(min_file_age=60, simulate_processing=args.simulate),
        workflow=WorkflowConfig(
            images=ImageWorkflowConfig(
                enable_geotagging=(
                    not args.disable_geotagging if args.disable_geotagging else True
                ),
                enable_face_recognition=True,
                enable_object_detection=False,
                enable_color_analysis=True,
                enable_captioning=False,
                enable_description=True,
                enable_tagging=True,
                enable_ocr=True,
                enable_rating=False,
                write_metadata=True,
                move_processed_media=True,
            ),
            videos=VideoWorkflowConfig(move_processed_media=False),
            general=GeneralWorkflowConfig(),
        ),
        logging=LoggingConfig(),
    )

    # Print final configuration
    print(json.dumps(asdict(config), indent=4))

    controller = MediaController(config)
    await controller.start()
    print("Media workflow started.")


if __name__ == "__main__":
    asyncio.run(main())
