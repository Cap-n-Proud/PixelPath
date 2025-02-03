# media_workflow/image_processor.py

# https://images.squarespace-cdn.com/content/v1/523c7f80e4b032ff8b3b0a97/1440518068126-5STUUQWOW8OKKVENBNJ2/citysign_001_2.jpg
# https://media.gettyimages.com/id/482804533/photo/fabulous-las-vegas-sign.jpg?s=612x612&w=0&k=20&c=7Aljht_9lgSgmPmhUFv3PPUDVnbgH01Ipjf3pH78ybs=

# Image tagging via Clarifai => OK
# AI caption generation
# OCR processing
# object:https://replicate.com/cudanexus/detic?prediction=v9wwtxn4vhrme0cmqhrsgk1764
# Face recognition/classification => OK
# Color analysis => OK
# GPS reverse geocoding => OK
# Metadata writing => OK
# exiftool -all= -overwrite_original file.jpg

from typing import Tuple

import json
import webcolors
import numpy as np
import face_recognition
from pathlib import Path
from typing import List, Dict, Optional
from PIL import Image
from sklearn import svm
from sklearn.cluster import KMeans
import pickle
import io
from metadata_service import MetadataService
from api_client import APIClient
from file_mananger import FileManager
import requests
from stop_timer import StopTimer


from clarifai_grpc.channel.clarifai_channel import ClarifaiChannel
from clarifai_grpc.grpc.api import resources_pb2, service_pb2, service_pb2_grpc
from clarifai_grpc.grpc.api.status import status_code_pb2

import logging
from log_service import setup_logging
from paddleocr import PaddleOCR


from libs.color_service import color_names_rgb, _create_color_mapping


class ImageProcessor:
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
        # Setup logging before using it
        setup_logging(config)  # Make sure logging is configured

        # Directly use the root logger
        self.logger = logging.getLogger()  # No need to use __name__ here
        self.color_names_rgb = color_names_rgb
        self._create_color_mapping = _create_color_mapping
        self.color_map = self._create_color_mapping()
        if self.config.workflow.images.enable_ocr:
            # Initialize PaddleOCR with English language support and angle classification
            self.ocr = PaddleOCR(
                use_angle_cls=True, lang="en", use_gpu=False
            )  # Force CPU
        self.logger.info(
            "Image Processor initialized with configuration: %s", self.config
        )

    async def process(self, image_path: Path) -> Dict:
        """Full image processing pipeline"""
        timer = StopTimer()

        # Start timing
        timer.start()
        results = {}
        self.logger.info("Started processing image %s", image_path)

        try:
            # Core processing steps
            if self.config.workflow.images.enable_tagging:
                results["tags"] = await self._get_image_tags(image_path)
                self.logger.debug(f"Tags: {results['tags']}")

            if self.config.workflow.images.enable_geotagging:
                results["geotag"] = await self._process_geotagging(image_path)

                self.logger.debug(f"Geotag: {results['geotag']}")

            if self.config.workflow.images.enable_description:
                results["description"] = await self._process_description(image_path)
                self.logger.debug(f"Description: {results['description']}")

            if self.config.workflow.images.enable_color_analysis:
                results["colors"] = await self._process_analyze_colors(image_path)
                self.logger.debug(f"Dominat colors: {results['colors']}")

            # if self.config.processing.detect_objects:
            #     results["objects"] = await self._detect_objects(image_path)

            if self.config.workflow.images.enable_face_recognition:
                results["faces"] = await self._classify_faces(image_path)
                self.logger.debug(f"Faces: {results['faces']}")

            # if self.config.processing.generate_captions:
            #     results["caption"] = await self._generate_caption(image_path)

            if self.config.workflow.images.enable_ocr:
                results["ocr"] = await self._process_ocr(image_path)
                self.logger.info(f"OCR: {results['ocr']}")

            # Write metadata
            if self.config.workflow.images.write_metadata and len(results):
                await self.metadata.write_metadata(image_path, results, "image")
            self.logger.info(f"Resuts: {results}")
        except Exception as e:
            self.logger.error(f"Image processing failed for {image_path}: {str(e)}")
            return {}
        # Stop timing after processing
        timer.stop()

        # Log the duration
        self.logger.info(
            "Finished processing image %s with results: %s", image_path, results
        )
        self.logger.info(
            "Time taken to process image %s: %s seconds", image_path, timer.duration()
        )

        # Reset the timer for next usage
        timer.reset()
        return results

    async def _process_description(self, image_path: Path) -> List[str]:
        import replicate

        prompt = self.config.processing.image_description_prompt

        # Step 1: Resize the image
        try:
            resized_image = await self.file_manager.resize_image(
                image_path, max_width=1920
            )

            self.logger.debug(resized_image[:300])
            resized_image = io.BytesIO(
                resized_image
            )  # ✅ Wrap bytes into a file-like object
        except Exception as e:
            error_message = (
                f"An exception occurred while resizing the image {image_path}: {str(e)}"
            )
            self.logger.error(error_message)
            return

        o = replicate.run(
            self.config.processing.replicate_model,
            input={
                "prompt": prompt,
                "image": resized_image,
            },
        )
        # The yorickvp/llava-13b model can stream output as it's running.
        # The predict method returns an iterator, and you can iterate over that output.
        output = ""
        for item in o:
            # https://replicate.com/yorickvp/llava-13b/versions/e272157381e2a3bf12df3a8edd1f38d1dbd736bbb7437277c8b34175f8fce358/api#output-schema
            # print(item, end="")
            output = output + item
        return output

    async def _get_image_tags(self, image_path: Path) -> List[str]:
        """Get image tags using Clarifai API"""

        resized_image = await self.file_manager.resize_image(image_path, max_width=1920)
        channel = ClarifaiChannel.get_json_channel()
        stub = service_pb2_grpc.V2Stub(ClarifaiChannel.get_grpc_channel())
        # This is how you authenticate.
        metadata = (("authorization", f"Key {self.config.api.CLARIFAI_API_KEY}"),)
        app_id = self.config.api.CLARIFAI_APP_ID

        post_model_outputs_response = stub.PostModelOutputs(
            service_pb2.PostModelOutputsRequest(
                model_id="general-image-recognition",
                # model_id="aaa03c23b3724a16a56b629203edc62c",
                user_app_id=resources_pb2.UserAppIDSet(app_id=app_id),
                inputs=[
                    resources_pb2.Input(
                        data=resources_pb2.Data(
                            image=resources_pb2.Image(base64=resized_image)
                        )
                    )
                ],
                model=resources_pb2.Model(
                    output_info=resources_pb2.OutputInfo(
                        output_config=resources_pb2.OutputConfig(
                            max_concepts=50, min_value=0.50
                        )
                    )
                ),
            ),
            metadata=metadata,
        )

        if post_model_outputs_response.status.code != status_code_pb2.SUCCESS:
            raise Exception(
                "Post model outputs failed, status: "
                + post_model_outputs_response.status.description
            )

        # Since we have one input, one output will exist here.
        output = post_model_outputs_response.outputs[0]
        tags = ""
        tagNames = []
        tagCount = 0
        # self.logger.debug("Predicted concepts:")
        for concept in output.data.concepts:
            tagCount += 1
            tagNames.append(concept.name)
        if len(tagNames) > 0:
            self.logger.debug(
                f"|Tag Image| {tagCount} tags generated: " + str(tagNames)
            )
        self.logger.debug("Tags generated for image %s: %s", image_path, tagNames)

        return tagNames

    async def _generate_caption(self, image_path: Path) -> Optional[str]:
        """Generate image caption using AI service"""
        try:
            payload = {
                "input": {
                    "image": str(image_path),
                    "model": self.config.processing.caption_model,
                }
            }

            response = await self.api.post_request(self.config.api.caption_url, payload)

            return response.get("caption") if response else None

        except Exception as e:
            self.logger.error(f"Caption generation failed: {str(e)}")
            return None

    async def process_ocr_output(self, ocr_output):
        # Flatten the nested list structure to get all text fragments with their confidence
        fragments = []
        for line in ocr_output[
            0
        ]:  # ocr_output is a list with one element which is a list of lines
            text, confidence = line[1]
            fragments.append({"text": text, "confidence": confidence})

        # Join texts where confidence exceeds the threshold
        ocrResult = " ".join(
            [
                fragment["text"]
                for fragment in fragments
                if fragment["confidence"] > self.config.processing.ocr_confidence
            ]
        )
        return ocrResult

    async def _process_ocr(self, image_path: Path) -> List[str]:
        """Perform OCR on image"""
        try:
            result = []

            # Perform OCR on the image
            ocr_output = self.ocr.ocr(str(image_path))
            self.logger.debug(f"|OCR Image| successful: {str(ocr_output)}")

            if ocr_output and ocr_output[0]:  # Check if OCR produced any results
                result = await self.process_ocr_output(ocr_output)
            else:
                self.logger.debug(
                    f"|OCR Image| No text detected in image: {image_path}"
                )
                result = ""  # Or return an empty list if you prefer

            return result
        except Exception as e:
            self.logger.error(f"|OCR Image| Error during OCR: {str(e)}")
            # Here you might want to return an empty list, or some error string
            return ["Error in OCR processing"]

        except Exception as e:
            self.logger.error(f"OCR processing failed: {str(e)}")
            return ""

    async def _classify_faces(self, image_path: Path) -> List[str]:
        """Face recognition and classification"""
        try:
            # Load or train classifier
            classifier = await self._get_face_classifier()

            # Process image
            image = face_recognition.load_image_file(image_path)
            face_encodings = face_recognition.face_encodings(image)

            if not face_encodings:

                return [self.config.processing.no_face_tag]

            # Predict faces
            predictions = classifier.predict(face_encodings)
            self.logger.debug(
                "Detected faces for image %s: %s", image_path, predictions
            )

            return list(set(predictions))

        except Exception as e:
            self.logger.error(f"Face classification failed: {str(e)}")
            return []

    async def _get_face_classifier(self):
        """Load or train face classifier"""
        if not self.config.paths.face_classifier.exists():
            self.logger.warning(
                f"No face classifier found in: {str(self.config.paths.face_classifier)} training a new one."
            )

            await self._train_face_classifier()

        with open(self.config.paths.face_classifier, "rb") as f:
            return pickle.load(f)

    async def _train_face_classifier(self):
        """Train new face classifier model"""
        encodings = []
        names = []

        for person_dir in self.config.paths.known_faces_dir.iterdir():
            if not person_dir.is_dir():
                continue

            for image_file in person_dir.glob("*"):
                image = face_recognition.load_image_file(image_file)
                face_encodings = face_recognition.face_encodings(image)

                if len(face_encodings) == 1:
                    encodings.append(face_encodings[0])
                    names.append(person_dir.name)

        classifier = svm.SVC(gamma="scale")
        classifier.fit(encodings, names)

        with open(self.config.paths.face_classifier, "wb") as f:
            pickle.dump(classifier, f)

    async def closest_color(self, rgb: np.ndarray) -> str:
        # Function to calculate the Euclidean distance between two colors
        def euclidean_distance(c1, c2):
            return np.sqrt(np.sum((np.array(c1) - np.array(c2)) ** 2))

        closest_color = None
        min_distance = float("inf")

        # Iterate through the color names and find the closest match
        for color_name, color_rgb in self.color_names_rgb.items():
            distance = euclidean_distance(rgb, color_rgb)
            if distance < min_distance:
                min_distance = distance
                closest_color = color_name

        return closest_color

    async def _process_analyze_colors(self, image_path: Path) -> List[str]:
        """Analyze dominant colors in image"""

        resized_image = await self.file_manager.resize_image(image_path, max_width=1920)
        resized_image = Image.open(
            io.BytesIO(resized_image)
        )  # ✅ Wrap bytes into a file-like object

        pixels = np.array(resized_image)
        # self.logger.debug(resized_image[:300])
        # self.logger.debug(pixels[:300])
        if pixels.size == 0:
            raise ValueError("Empty or corrupt image file")
        # Ensure it's in the expected shape (height, width, channels)
        if len(pixels.shape) != 3:
            raise ValueError(f"Unexpected image shape: {pixels.shape}")

        # Handle alpha channel
        if pixels.shape[-1] == 4:
            pixels = pixels[..., :3]

        pixels = pixels.reshape(-1, 3)
        # Apply K-means clustering to find the dominant colors
        k = 4
        n = 5
        kmeans = KMeans(n_clusters=k, n_init="auto").fit(pixels)
        # Get the colors of the cluster centers
        colors = kmeans.cluster_centers_
        # Get the count of pixels assigned to each cluster
        labels, counts = np.unique(kmeans.labels_, return_counts=True)
        # Sort the colors by frequency
        sorted_colors = colors[np.argsort(-counts)]
        # Convert the color values to integers and map to color names

        color_names = [
            await self.closest_color(np.round(color).astype(int))
            for color in sorted_colors
        ]
        # print(sorted_colors)

        # Return the top n colors
        top_colors = color_names[:n]
        simpleColors = []

        try:
            for color in top_colors:
                simpleColors.append(self.COLORS[color])
        except:
            pass
        top_colors += simpleColors
        top_colors = list(set(top_colors))
        self.logger.debug("|Top Colors|: " + str(top_colors))

        return top_colors

    async def _process_geotaggingALT(self, image_path: Path) -> Dict:
        """Handle reverse geocoding and return structured location components as a dictionary"""
        gps_data = self.metadata.get_gps_coordinates(image_path)

        if not gps_data:
            self.logger.debug(f"No GPS data in {image_path}")
            return {}

        # Validate coordinates
        try:
            lat = gps_data["lat"]
            lon = gps_data["lon"]
        except KeyError:
            self.logger.error(f"Invalid GPS data in {image_path}: {gps_data}")
            return {}

        self.logger.debug(
            f"Processing geotagging for {image_path} with coordinates {lat},{lon}"
        )

        # Build API endpoint
        endpoint = (
            f"{self.config.api.reverse_geo_url}{lat},{lon}"
            f"&key={self.config.api.REVERSE_GEO_API_KEY}"
        )

        try:
            response = await self.api.post_request(endpoint, {})

            # Validate response structure
            if not response.get("results"):
                self.logger.warning(f"No geocoding results for {image_path}")
                return {}

            first_result = response["results"][0]
            components = first_result.get("components", {})

            self.logger.debug(f"Geocoding components for {image_path}: {components}")
            return components

        except IndexError:
            self.logger.error(f"Malformed geocoding response for {image_path}")
            return {}
        except KeyError as e:
            self.logger.error(f"Missing expected key in geocoding response: {str(e)}")
            return {}
        except Exception as e:
            self.logger.error(f"Geotagging failed for {image_path}: {str(e)}")
            return {}

    async def _process_geotagging(self, image_path: Path) -> Dict:
        """Handle reverse geocoding"""
        gps_data = await self.metadata.get_gps_coordinates(image_path)
        if not gps_data:
            self.logger.warning("No GPS data found for image %s", image_path)

            return []
        endpoint = f"{self.config.api.reverse_geo_url}{gps_data.get('lat')},{gps_data.get('lon')}&key={self.config.api.REVERSE_GEO_API_KEY}"
        try:
            response = await self.api.post_request(endpoint, {})
            # Extracting relevant information
            geolocation = response["results"][0]["components"]
            # print(geolocation)
            reverse_geo = [
                value for key, value in response["results"][0]["components"].items()
            ]
            self.logger.debug("Geotag data for image %s: %s", image_path, geolocation)

            return geolocation

        except Exception as e:
            self.logger.error(f"Geotagging failed: {str(e)}")
            return []
