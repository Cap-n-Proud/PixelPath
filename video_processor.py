# Scene detection with AdaptiveDetector

# Fallback sampling strategy

# Audio extraction with FFmpeg

# Whisper-based transcription

# Frame analysis for objects/faces

# Color palette generation

# Metadata embedding

# media_workflow/video_processor.py
import logging
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional
import cv2
import numpy as np

from scenedetect import VideoManager, SceneManager, AdaptiveDetector
from scenedetect.scene_manager import save_images
from .metadata_service import MetadataService
from .api_client import APIClient
from .file_manager import FileManager


class VideoProcessor:
    def __init__(
        self,
        config,
        metadata: MetadataService,
        api: APIClient,
        file_manager: FileManager,
    ):
        self.config = config
        self.metadata = metadata
        self.api = api
        self.file_manager = file_manager
        self.logger = logging.getLogger(__name__)

    async def process(self, video_path: Path) -> Dict:
        """Full video processing pipeline"""
        results = {}
        temp_dir = None

        try:
            temp_dir = self.file_manager.create_temp_dir(video_path.stem)

            # Core processing steps
            scene_data = await self._detect_scenes(video_path, temp_dir)
            audio_path = await self._extract_audio(video_path, temp_dir)

            results.update(
                {
                    "scenes": scene_data["scenes"],
                    "frames": scene_data["frames"],
                    "transcription": await self._transcribe_audio(audio_path),
                    "objects": await self._process_scene_analysis(temp_dir),
                    "colors": await self._analyze_scene_colors(temp_dir),
                }
            )

            # Write metadata
            await self._write_video_metadata(video_path, results)

            return results

        except Exception as e:
            self.logger.error(f"Video processing failed for {video_path}: {str(e)}")
            return {}
        finally:
            if temp_dir:
                await self.file_manager.cleanup_temp_dir(temp_dir)

    async def _detect_scenes(self, video_path: Path, output_dir: Path) -> Dict:
        """Detect scenes and extract key frames"""
        try:
            video_manager = VideoManager([str(video_path)])
            scene_manager = SceneManager()
            scene_manager.add_detector(
                AdaptiveDetector(
                    adaptive_threshold=self.config.processing.scene_threshold,
                    min_scene_len=self.config.processing.min_scene_length,
                )
            )

            video_manager.set_downscale_factor()
            video_manager.start()
            scene_manager.detect_scenes(frame_source=video_manager)
            scene_list = scene_manager.get_scene_list()

            if len(scene_list) >= self.config.processing.min_scenes:
                frame_files = save_images(
                    scene_list,
                    video_manager,
                    output_dir=str(output_dir),
                    num_images=1,
                    image_extension="jpg",
                )
                return {
                    "scenes": [scene[1].get_timecode() for scene in scene_list],
                    "frames": [Path(f) for f in frame_files],
                }

            return await self._fallback_sampling(video_path, output_dir)

        except Exception as e:
            self.logger.error(f"Scene detection failed: {str(e)}")
            return await self._fallback_sampling(video_path, output_dir)

    async def _fallback_sampling(self, video_path: Path, output_dir: Path) -> Dict:
        """Fallback frame sampling strategy"""
        try:
            frames = []
            cap = cv2.VideoCapture(str(video_path))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

            for ratio in self.config.processing.sampling_strategy:
                frame_pos = int(total_frames * ratio)
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_pos)
                ret, frame = cap.read()
                if ret:
                    frame_path = output_dir / f"frame_{ratio*100:.0f}.jpg"
                    cv2.imwrite(str(frame_path), frame)
                    frames.append(frame_path)

            return {"scenes": ["full_video"], "frames": frames}
        except Exception as e:
            self.logger.error(f"Fallback sampling failed: {str(e)}")
            return {"scenes": [], "frames": []}

    async def _extract_audio(
        self, video_path: Path, output_dir: Path
    ) -> Optional[Path]:
        """Extract audio track from video"""
        audio_path = output_dir / "audio.aac"

        try:
            cmd = [
                "ffmpeg",
                "-y",
                "-i",
                str(video_path),
                "-vn",
                "-acodec",
                "copy",
                "-loglevel",
                "error",
                str(audio_path),
            ]

            process = await asyncio.create_subprocess_exec(
                *cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE
            )

            _, stderr = await process.communicate()
            if process.returncode != 0:
                raise RuntimeError(f"FFmpeg error: {stderr.decode()}")

            return audio_path
        except Exception as e:
            self.logger.error(f"Audio extraction failed: {str(e)}")
            return None

    async def _transcribe_audio(self, audio_path: Optional[Path]) -> str:
        """Transcribe audio using API"""
        if not audio_path or not audio_path.exists():
            return ""

        try:
            model_size = (
                "large"
                if audio_path.stat().st_size
                < self.config.processing.transcribe_size_threshold
                else "medium"
            )

            response = await self.api.post_request(
                self.config.api.transcribe_url,
                {"audio": str(audio_path), "model": model_size},
            )

            return response.get("transcription", "") if response else ""
        except Exception as e:
            self.logger.error(f"Transcription failed: {str(e)}")
            return ""

    async def _process_scene_analysis(self, scene_dir: Path) -> Dict:
        """Analyze extracted frames for objects and faces"""
        results = {"objects": [], "faces": []}

        try:
            for frame in scene_dir.glob("*.jpg"):
                # Process objects
                obj_response = await self.api.post_request(
                    self.config.api.obj_detection_url, {"image": str(frame)}
                )
                if obj_response:
                    results["objects"].extend(obj_response.get("objects", []))

                # Process faces
                face_response = await self.api.post_request(
                    self.config.api.face_detection_url, {"image": str(frame)}
                )
                if face_response:
                    results["faces"].extend(face_response.get("faces", []))

            # Deduplicate results
            results["objects"] = list(set(results["objects"]))
            results["faces"] = list(set(results["faces"]))

            return results
        except Exception as e:
            self.logger.error(f"Scene analysis failed: {str(e)}")
            return results

    async def _analyze_scene_colors(self, scene_dir: Path) -> List[str]:
        """Analyze dominant colors across all frames"""
        try:
            color_samples = []
            for frame in scene_dir.glob("*.jpg"):
                img = cv2.imread(str(frame))
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                pixels = img.reshape(-1, 3)
                color_samples.extend(pixels[np.random.choice(pixels.shape[0], 100)])

            kmeans = KMeans(
                n_clusters=3,
                n_init=10,
                random_state=self.config.processing.color_analysis_seed,
            )
            kmeans.fit(color_samples)

            return [self._rgb_to_hex(center) for center in kmeans.cluster_centers_]
        except Exception as e:
            self.logger.error(f"Color analysis failed: {str(e)}")
            return []

    def _rgb_to_hex(self, rgb: np.ndarray) -> str:
        """Convert RGB array to hexadecimal color code"""
        return "#{:02x}{:02x}{:02x}".format(int(rgb[0]), int(rgb[1]), int(rgb[2]))

    async def _write_video_metadata(self, video_path: Path, results: Dict):
        """Write processed results to video metadata"""
        metadata = {
            "description": self._format_description(results),
            "keywords": self._extract_keywords(results),
        }

        try:
            self.metadata.write_metadata(video_path, metadata, "video")
        except Exception as e:
            self.logger.error(f"Metadata write failed: {str(e)}")

    def _format_description(self, results: Dict) -> str:
        """Format video description from analysis results"""
        description = []

        if results.get("transcription"):
            description.append(f"[TRANSCRIPTION]\n{results['transcription']}")

        if results.get("objects"):
            description.append(f"[OBJECTS]\n{', '.join(results['objects'])}")

        if results.get("colors"):
            description.append(f"[COLORS]\n{', '.join(results['colors'])}")

        return "\n\n".join(description)

    def _extract_keywords(self, results: Dict) -> List[str]:
        """Extract keywords from analysis results"""
        keywords = []

        if results.get("scenes"):
            keywords.extend([f"scene_{i+1}" for i in range(len(results["scenes"]))])

        if results.get("faces"):
            keywords.extend(results["faces"])

        if results.get("objects"):
            keywords.extend(results["objects"])

        return list(set(keywords))


# # Configuration
# config = AppConfig(
#     processing=ProcessingConfig(
#         scene_threshold=2.0,
#         min_scenes=3,
#         sampling_strategy=[0.1, 0.5, 0.9],
#         transcribe_size_threshold=20,  # MB
#         color_analysis_seed=42,
#     ),
#     api=ApiConfig(
#         transcribe_url="https://whisper-api/transcribe",
#         obj_detection_url="https://vision-api/detect",
#         face_detection_url="https://face-api/detect",
#     ),
# )

# # Initialize services
# metadata = MetadataService(config)
# api = APIClient(config)
# file_manager = FileManager(config)

# # Process video
# processor = VideoProcessor(config, metadata, api, file_manager)
# results = await processor.process(Path("/path/to/video.mp4"))

# print(f"Detected {len(results['scenes'])} scenes")
# print(f"Transcription: {results['transcription'][:100]}...")
