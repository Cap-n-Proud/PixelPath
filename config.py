# config.py
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import List, Optional, Dict


@dataclass
class ApiConfig:
    """Configuration for external API services"""

    caption_url: str
    ocr_url: str
    obj_detection_url: str
    reverse_geo_url: str
    REVERSE_GEO_API_KEY: str
    rating_url: str
    face_detection_url: str
    clarifai_url: str
    CLARIFAI_API_KEY: str
    CLARIFAI_APP_ID: str
    wisper_url: str
    image_server_url: str
    wisper_model: str = "medium"
    # ["tiny", "base", "small", "medium", "large-v1", "large-v2"]
    clarifai_model: str = "general-image-recognition"
    caption_model: str = "blip-large"
    caption_header: str = '{"content-type": "application/json"}'
    ocr_header: str = '{"content-type": "application/json"}'
    rating_header: str = '{"content-type": "application/json"}'
    obj_detection_header: str = '{"content-type": "application/json"}'
    transcribe_header: str = '{"content-type": "application/json"}'


@dataclass
class PathConfig:
    """File system paths configuration"""

    watch_dir: Path
    image_dest: Path
    video_dest: Path
    ramdisk_dir: Path
    log_dir: Path
    face_classifier: Path
    known_faces_dir: Path
    unknown_faces_dir: Path
    temp_dir: Path
    secrets_path: Path


@dataclass
class ProcessingConfig:
    """Media processing parameters"""

    # Image processing
    face_distance_threshold: float = 0.5
    max_faces: int = 10
    colors_to_detect: int = 5
    ocr_confidence: float = 0.7
    ocr_lang: str = "en"
    image_rating_overwrite: bool = False
    obj_confidence: float = 0.7
    obj_detection_model_name: str = "yolox-x"
    min_face_size: int = 100  # pixels
    unknown_face_tag: str = "unknown_face"
    no_face_tag: str = "no_faces"
    # image_description_prompt: str = (
    #     "As a distinguished photographer and art critic, you are entrusted with curating a collection of compelling photographs. Your role is to write insightful descriptions that delve deeply into the emotional essence of each image, capturing the feelings it evokes in viewers. Assess the photographs carefully, focusing on both their artistic and technical qualities. Highlight specific elements that enhance or detract from the emotional impact. Conclude your evaluation with a thoughtful reflection on how the photograph's emotional weight could be deepened or sustained , but only suggest improvements if genuinely warranted. If no improvements are required, offer commentary on why the image is emotionally effective as it stands. Avoid vague recommendations like 'change perspective' or 'add more context.' Instead, provide clear, actionable suggestions that address both technical precision and emotional resonance when necessary. Be mindful to point out locations or recognizable landmarks where applicable to enrich the viewer's connection to the image.Keep your assessment concise and articulate, ensuring it doesn’t exceed 2,500 characters."
    # )
    image_description_prompt = """
Imagine you are a photographer, art critic, visual artist, and storyteller. Your task is to craft descriptions that capture the essence of each image, focusing on the emotions, cultural significance, and storytelling elements evoked.

1. **Analyze Technical & Artistic Elements:** Examine aspects like lighting, composition, and color palette. How do these elements contribute to the mood or narrative? For example, does the warm lighting create a comforting atmosphere?

2. **Highlight Emotional Impact:** Identify how specific elements enhance or detract from the emotional resonance. Mention details like shadows that evoke mystery or vibrant colors that convey joy.

3. **Provide Actionable Feedback:** If improvements are needed, suggest practical changes such as adjusting lighting angles to emphasize texture or incorporating weather details to set a scene's tone.

4. **Incorporate Contextual Clues:** Include recognizable landmarks, time of day, or weather conditions to enrich the viewer’s connection and understanding of the image without overwhelming with information.

5. **Concise & Streamlined:** Ensure your descriptions are clear, specific, and within 2500 characters, balancing depth with brevity.

By integrating these elements, each description will offer a rich, multifaceted exploration of the photograph, enhancing both technical precision and emotional resonance.
"""

    replicate_model: str = (
        "yorickvp/llava-13b:e272157381e2a3bf12df3a8edd1f38d1dbd736bbb7437277c8b34175f8fce358"
    )

    # Video processing
    scene_threshold: float = 2.0
    min_scene_length: int = 15  # frames
    min_scenes: int = 2
    sampling_strategy: List[float] = (0.1, 0.5, 0.9)
    frames_per_second: float = 0.2
    transcribe_size_threshold: int = 50  # MB

    # General
    max_retries: int = 3
    timeout: int = 30  # seconds
    min_file_age: int = 60  # seconds
    metadata_behavior: str = "append"
    simulate_processing: bool = True
    recursive_search: bool = True
    conflict_resolution: str = "overwrite"
    rename_suffix: str = "_{counter}"
    watch_interval: int = 5  # seconds
    ramdisk_size: int = 512


@dataclass
class ImageWorkflowConfig:
    """Image processing workflow settings"""

    enable_geotagging: bool = True
    enable_face_recognition: bool = True
    enable_object_detection: bool = True
    enable_color_analysis: bool = True
    enable_captioning: bool = True
    enable_description: bool = True
    enable_tagging: bool = True
    enable_ocr: bool = True
    enable_rating: bool = True
    write_metadata: bool = True
    move_processed_media: bool = True


@dataclass
class VideoWorkflowConfig:
    """Video processing workflow settings"""

    enable_geotagging: bool = True
    enable_face_recognition: bool = True
    enable_object_detection: bool = True
    enable_color_analysis: bool = True
    enable_captioning: bool = True
    enable_description: bool = True
    enable_tagging: bool = True
    enable_ocr: bool = True
    # enable_rating: bool = True
    write_metadata: bool = True
    move_processed_media: bool = True
    enable_transcription: bool = True
    # enable_frame_analysis: bool = True
    write_metadata: bool = True
    move_processed_media: bool = True


@dataclass
class GeneralWorkflowConfig:
    """General workflow settings"""

    create_sidecar_files: bool = True
    preserve_originals: bool = False


@dataclass
class WorkflowConfig:
    """Main workflow configuration grouping"""

    images: ImageWorkflowConfig = field(default_factory=ImageWorkflowConfig)
    videos: VideoWorkflowConfig = field(default_factory=VideoWorkflowConfig)
    general: GeneralWorkflowConfig = field(default_factory=GeneralWorkflowConfig)


@dataclass
class LoggingConfig:
    """Logging configuration"""

    level: str = "INFO"
    max_size: int = 10  # MB
    backup_count: int = 5
    format: str = "[%(asctime)s][%(name)s][%(levelname)s] %(message)s"


@dataclass
class AppConfig:
    """Root application configuration"""

    api: ApiConfig = field(default_factory=ApiConfig)
    paths: PathConfig = field(default_factory=PathConfig)
    processing: ProcessingConfig = field(default_factory=ProcessingConfig)
    workflow: WorkflowConfig = field(default_factory=WorkflowConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)

    # Derived properties
    @property
    def image_extensions(self) -> tuple:
        return (".jpg", ".jpeg", ".png", ".heic", ".webp")

    @property
    def video_extensions(self) -> tuple:
        return (".mp4", ".mov", ".avi", ".mkv")
