# media_workflow/api_client.py
import httpx
import logging
from typing import Optional, Any
from pathlib import Path

import logging
from log_service import setup_logging


class APIClient:
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.client = httpx.AsyncClient(timeout=30)
        # Setup logging before using it
        setup_logging(config)  # Make sure logging is configured

        # Directly use the root logger
        self.logger = logging.getLogger()  # No need to use __name__ here

    async def post_request(self, endpoint: str, payload: dict) -> Optional[dict]:
        try:
            resp = await self.client.post(endpoint)
            resp.raise_for_status()
            return resp.json()
        except httpx.RequestError as e:
            self.logger.error(f"API request failed: {e}")
            return None

    async def get_request(self, endpoint: str, payload: dict) -> Optional[dict]:
        try:
            resp = await self.client.get(endpoint)
            resp.raise_for_status()
            return resp.json()
        except httpx.RequestError as e:
            self.logger.error(f"API request failed: {e}")
            return None

    async def get_image_analysis(
        self, image_path: Path, service_type: str
    ) -> Optional[dict]:
        url = getattr(self.config.api, f"{service_type}_url")
        payload = {
            "image": str(image_path),
            "confidence": self.config.processing.obj_confidence,
        }
        return await self.post_request(url, payload)

    async def transcribe_audio(self, audio_path: Path) -> Optional[str]:
        payload = {"audio": str(audio_path), "model": "medium"}  # Configurable
        response = await self.post_request(self.config.api.transcribe_url, payload)
        return response.get("transcription") if response else None
