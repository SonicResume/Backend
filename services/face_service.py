from insightface.app import FaceAnalysis
import numpy as np

app = FaceAnalysis(name="buffalo_l")
app.prepare(ctx_id=0, det_size=(640, 640))

def extract_face(img):
    faces = app.get(img)
    if not faces:
        return None
    return faces[0].embedding
