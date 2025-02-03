# Media Processing Pipeline

Automated workflow for photo and video processing with AI-powered tagging, captioning, OCR, and metadata management.

![Workflow Diagram](docs/workflow.png)

## Features

- **Image Processing**  
  - Auto-tagging with Clarifai/YOLOX
  - GPT-4 powered artistic commentary
  - Face recognition & classification
  - Reverse geocoding (OpenCage)
  - Color palette extraction
  - EXIF/IPTC metadata handling

- **Video Processing**  
  - Scene detection & keyframe extraction
  - Audio transcription (Whisper)
  - Object detection in video frames
  - Metadata embedding in QuickTime files

- **Core Infrastructure**  
  - Async task processing (5 concurrent workers)
  - Configurable file organization
  - RAM disk for temp processing
  - Unified logging & error handling

## Installation

```bash
# Clone repo
git clone https://github.com/yourusername/media-pipeline.git
cd media-pipeline

# Create virtual env
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt