import cv2
import time
import numpy as np
from insightface.app import FaceAnalysis

class RealtimeFaceEngine:
    def __init__(self, face_model: FaceAnalysis, faiss_index=None):
        self.face = face_model
        self.index = faiss_index

    def process_frame(self, frame):
        faces = self.face.get(frame)

        results = []

        for f in faces:
            emb = f.embedding
            emb = emb / (np.linalg.norm(emb) + 1e-8)

            match = None
            score = 0

            if self.index:
                res = self.index.search(emb, 1)
                if res:
                    match = res[0]["user_id"]
                    score = res[0]["score"]

            x1, y1, x2, y2 = map(int, f.bbox)

            results.append({
                "bbox": [x1, y1, x2, y2],
                "match": match,
                "score": float(score)
            })

        return results
