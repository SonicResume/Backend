import modal
import numpy as np
import cv2
from insightface.app import FaceAnalysis

app = modal.App("face-gpu")

image = (
    modal.Image.debian_slim()
    .pip_install(
        "insightface",
        "opencv-python-headless",
        "numpy",
        "onnxruntime"
    )
)

@app.cls(image=image, gpu="A10G")
class FaceService:

    def __enter__(self):
        self.model = FaceAnalysis(name="buffalo_l")
        self.model.prepare(ctx_id=0, det_size=(640, 640))

    @modal.method()
    def embed(self, image_bytes: bytes):
        img = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(img, cv2.IMREAD_COLOR)

        faces = self.model.get(img)
        if not faces:
            return {"error": "no_face"}

        emb = faces[0].embedding
        emb = emb / (np.linalg.norm(emb) + 1e-8)

        return emb.tolist()
