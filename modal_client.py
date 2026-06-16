import modal
import cv2
import numpy as np

# connect to deployed Modal class
face_cls = modal.Cls.from_name("face-embedder", "FaceService")


def embed_image_bytes(image_bytes: bytes):
    """
    Sends image to Modal GPU and returns embedding
    """

    try:
        result = face_cls.embed.remote(image_bytes)
        return result
    except Exception as e:
        print("Modal error:", e)
        return None
