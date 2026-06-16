import modal
import numpy as np
import cv2

app = modal.App("face-gpu")

# -------------------------
# SAFE IMAGE (FIXES "python not found")
# -------------------------
image = (
    modal.Image.debian_slim(python_version="3.10")
    .apt_install("git", "curl", "python3-pip")
    .run_commands("pip3 install --upgrade pip")
    .pip_install(
        "insightface==0.7.3",
        "numpy",
        "opencv-python-headless",
        "onnxruntime"   # CPU stable (NO GPU yet)
    )
)

# -------------------------
# FACE SERVICE
# -------------------------
@app.cls(image=image, gpu=None, timeout=300)
class FaceService:

    # -------------------------
    # LOAD MODEL ONCE
    # -------------------------
    @modal.enter()
    def setup(self):
        print("[MODAL] loading model...")

        from insightface.app import FaceAnalysis

        self.model = FaceAnalysis(name="buffalo_l")

        # CPU SAFE MODE FIRST
        self.model.prepare(ctx_id=-1, det_size=(640, 640))

        print("[MODAL] model ready")

    # -------------------------
    # EMBED FACE
    # -------------------------
    @modal.method()
    def embed(self, image_bytes: bytes):
        print("[MODAL] embed request")

        img = cv2.imdecode(
            np.frombuffer(image_bytes, np.uint8),
            cv2.IMREAD_COLOR
        )

        if img is None:
            return {"error": "decode_failed"}

        faces = self.model.get(img)

        if len(faces) == 0:
            return {"error": "no_face"}

        emb = faces[0].embedding
        emb = emb / (np.linalg.norm(emb) + 1e-8)

        return emb.tolist()

    # -------------------------
    # DETECT ONLY
    # -------------------------
    @modal.method()
    def detect(self, image_bytes: bytes):
        img = cv2.imdecode(
            np.frombuffer(image_bytes, np.uint8),
            cv2.IMREAD_COLOR
        )

        faces = self.model.get(img)

        return [
            {
                "bbox": f.bbox.tolist(),
                "score": float(f.det_score)
            }
            for f in faces
        ]
