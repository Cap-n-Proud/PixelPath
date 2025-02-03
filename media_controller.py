import asyncio
from pathlib import Path
import time

from config import AppConfig
from file_mananger import FileManager
from task_runner import TaskRunner
from metadata_service import MetadataService
from api_client import APIClient
from image_processor import ImageProcessor
import logging
from log_service import setup_logging
import os


class MediaController:
    def __init__(self, config: AppConfig):
        self.config = config

        # Setup logging before using it
        setup_logging(config)  # Make sure logging is configured

        # Directly use the root logger
        self.logger = logging.getLogger()  # No need to use __name__ here

        # Initialize dependencies
        self.file_manager = FileManager(config)
        self.metadata = MetadataService(config)
        self.api = APIClient(config)
        self.image_processor = ImageProcessor(
            config, self.metadata, self.api, self.file_manager
        )
        # self.video_processor = VideoProcessor(config, self.file_manager)
        self.task_runner = TaskRunner(self.config, max_concurrent=1)

        # Set to track processed files
        self.processed_files = set()

    async def start(self):
        """Main entry point to start processing"""
        self.logger.info("Starting media workflow")
        await asyncio.gather(self._watch_directory(), self.task_runner.run())

    async def _watch_directory(self):
        while True:
            for file_path in self._find_new_files():
                await self._process_file(file_path)
            await asyncio.sleep(self.config.processing.watch_interval)

    def _find_new_files(self) -> list[Path]:
        """Finds new files in the input folder, optionally recursively, that are older than the configured file age."""
        input_path = Path(self.config.paths.watch_dir)
        min_age = self.config.processing.min_file_age  # Age in seconds
        now = time.time()

        if not input_path.exists() or not input_path.is_dir():
            self.logger.warning(
                f"Input folder {input_path} does not exist or is not a directory."
            )
            return []

        new_files = []
        if self.config.processing.recursive_search:
            for root, _, files in os.walk(input_path):
                for filename in files:
                    file_path = Path(root) / filename
                    file_age = now - file_path.stat().st_mtime
                    if (
                        file_age >= min_age
                        and str(file_path) not in self.processed_files
                    ):
                        new_files.append(file_path)
                    else:
                        self.logger.debug(
                            f"Skipping {file_path} (too recent, age: {file_age:.2f}s or already processed)"
                        )
        else:
            for file_path in input_path.iterdir():
                if file_path.is_file():
                    file_age = now - file_path.stat().st_mtime
                    if (
                        file_age >= min_age
                        and str(file_path) not in self.processed_files
                    ):
                        new_files.append(file_path)
                    else:
                        self.logger.debug(
                            f"Skipping {file_path} (too recent, age: {file_age:.2f}s or already processed)"
                        )

        # Sort the new_files list alphabetically by the full path
        return sorted(new_files, key=lambda path: str(path))

    async def _process_file(self, file_path: Path):
        media_type = (
            "image" if file_path.suffix in self.config.image_extensions else "video"
        )
        # Check if the file has already been processed
        if str(file_path) in self.processed_files:
            self.logger.debug(f"File {file_path} has already been processed, skipping.")
            return

        if (
            self.config.workflow.images.move_processed_media
            or self.config.workflow.videos.move_processed_media
        ) and not self.config.processing.simulate_processing:
            file_path = await self.file_manager.organize_file(file_path, media_type)

        await self.task_runner.add_task(
            lambda: self._process_media(file_path, media_type)
        )

    async def _process_media(self, file_path: Path, media_type: str):
        try:

            if self.config.processing.simulate_processing:
                self.logger.info(
                    f"Simulating processing for {file_path} ({media_type})"
                )
                results = {"status": "simulated", "file": str(file_path)}
            else:
                if media_type == "image":
                    results = await self.image_processor.process(file_path)

                else:
                    pass
                    # results = await self.video_processor.process(file_path)
                # self.metadata.write_metadata(file_path, results, media_type)
                pass
                # Mark the file as processed only if processing was successful
            self.processed_files.add(str(file_path))
        except Exception as e:
            self.logger.error(f"Failed processing {file_path}: {e}")
            self.processed_files.add(str(file_path))
