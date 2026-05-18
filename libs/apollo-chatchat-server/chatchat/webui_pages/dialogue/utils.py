import base64
import os
from io import BytesIO

import streamlit as st


def encode_file_to_base64(file):
    # Encode file content as Base64
    buffer = BytesIO()
    buffer.write(file.read())
    return base64.b64encode(buffer.getvalue()).decode()


def process_files(files):
    result = {"videos": [], "images": [], "audios": []}
    for file in files:
        file_extension = os.path.splitext(file.name)[1].lower()

        # Detect the file type and process it accordingly
        if file_extension in [".mp4", ".avi"]:
            # Video file processing
            video_base64 = encode_file_to_base64(file)
            result["videos"].append(video_base64)
        elif file_extension in [".jpg", ".png", ".jpeg"]:
            # Image file processing
            image_base64 = encode_file_to_base64(file)
            result["images"].append(image_base64)
        elif file_extension in [".mp3", ".wav", ".ogg", ".flac"]:
            # Audio file processing
            audio_base64 = encode_file_to_base64(file)
            result["audios"].append(audio_base64)

    return result
