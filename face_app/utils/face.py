import insightface
import numpy as np

app = insightface.app.FaceAnalysis()
app.prepare(ctx_id=0, det_size=(640, 640))

def get_embedding(img):
    faces = app.get(img)
    if len(faces) == 0:
        return None
    return faces[0].embedding
