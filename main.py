# cd /mnt/Software/200-Apps/media_workflow/
# source venv/bin/activate
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
from config import AppConfig
from file_mananger import FileManager

# from image_processor import ImageProcessor
# from video_processor import VideoProcessor
from task_runner import TaskRunner
from metadata_service import MetadataService
from api_client import APIClient

from pathlib import Path
import asyncio
import json
from dataclasses import asdict
import os

from dotenv import load_dotenv

load_dotenv()
CLARIFAI_API_KEY = os.getenv("CLARIFAI_API_KEY")
CLARIFAI_APP_ID = os.getenv("CLARIFAI_APP_ID")
REVERSE_GEO_API_KEY = os.getenv("REVERSE_GEO_API_KEY")
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN")


async def main():
    controller = MediaController(config)
    await controller.start()
    print("started")


def serialize_config(config):
    """Recursively converts Path objects to strings in a dictionary"""

    def convert(obj):
        if isinstance(obj, Path):
            return str(obj)  # Convert Path to string
        if isinstance(obj, dict):
            return {k: convert(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [convert(v) for v in obj]
        return obj

    return convert(asdict(config))


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
        # watch_dir=Path("/mnt/Photos/001-Process/IN/"),
        watch_dir=Path("/mnt/Photos/005-PhotoBook/2008/"),
        # image_dest=Path("/mnt/Photos/001-Process/OUT/"),
        image_dest=Path("/mnt/Photos/005-PhotoBook/"),
        video_dest=Path("/mnt/Photos/010-Videos/"),
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
    processing=ProcessingConfig(min_file_age=60, simulate_processing=False),
    workflow=WorkflowConfig(
        # images=ImageWorkflowConfig(
        #     enable_geotagging=True,
        #     enable_face_recognition=True,
        #     enable_object_detection=True,
        #     enable_color_analysis=True,
        #     enable_captioning=True,
        #     enable_description=True,
        #     enable_tagging=True,
        #     enable_ocr=True,
        #     enable_rating=True,
        #     write_metadata=True,
        #     move_processed_media=True,
        images=ImageWorkflowConfig(
            enable_geotagging=False,
            enable_face_recognition=False,
            enable_object_detection=False,
            enable_color_analysis=False,
            enable_captioning=False,
            enable_description=False,
            enable_tagging=False,
            enable_ocr=True,
            enable_rating=False,
            write_metadata=True,
            move_processed_media=False,
        ),
        videos=VideoWorkflowConfig(
            move_processed_media=False,
        ),
        general=GeneralWorkflowConfig(),
    ),
    logging=LoggingConfig(),
)

# Convert paths before dumping to JSON
print(json.dumps(serialize_config(config), indent=4))

print("Enable Image Geotagging:", config.workflow.images.enable_geotagging)
print("Preserve Originals:", config.workflow.general.preserve_originals)
print("Simulation:", config.processing.simulate_processing)
print("Image Extension:", config.image_extensions)


# Initialize dependencies
metadata = MetadataService(config)
api = APIClient(config)
file_manager = FileManager(config)
# image_processor = ImageProcessor(config)
task_runner = TaskRunner(config, 1)


if __name__ == "__main__":
    asyncio.run(main())
