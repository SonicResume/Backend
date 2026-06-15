from fastapi import FastAPI, File, UploadFile, HTTPException
import cv2
import numpy as np
import onnxruntime as ort
from insightface.app import FaceAnalysis
import database

app = FastAPI(title="Biometric Matrix Engine")

# =========================
# GPU SAFE INIT
# =========================
providers = ort.get_available_providers()

face_engine = FaceAnalysis(
    name='buffalo_l',
    providers=providers
)

face_engine.prepare(ctx_id=0, det_size=(640, 640))

database.init_db()


# =========================
# EMBEDDING EXTRACTION
# =========================
def extract_embedding(file_bytes: bytes):
    nparr = np.frombuffer(file_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img is None:
        raise HTTPException(400, "INVALID_IMAGE")

    faces = face_engine.get(img)
    if not faces:
        raise HTTPException(404, "NO_FACE_DETECTED")

    emb = faces[0].embedding
    emb = emb / np.linalg.norm(emb)  # normalize ONCE

    return emb


# =========================
# REGISTER
# =========================
@app.post("/api/face/register")
async def register_face(user_id: str, name: str, file: UploadFile = File(...)):
    file_bytes = await file.read()
    embedding = extract_embedding(file_bytes)

    database.register_face_vector(user_id, name, embedding)
    return {"status": "ok"}


# =========================
# VERIFY
# =========================
@app.post("/api/face/verify")
async def verify_face(file: UploadFile = File(...)):
    probe = extract_embedding(await file.read())

    faces = database.get_all_registered_faces()

    if not faces:
        raise HTTPException(400, "EMPTY_DB")

    best = None
    best_score = -1.0

    THRESHOLD = 0.60

    for r in faces:
        score = float(np.dot(probe, np.array(r["embedding"])))

        if score > best_score:
            best_score = score
            best = r

    if best_score >= THRESHOLD:
        return {
            "verified": True,
            "user_id": best["user_id"],
            "name": best["name"],
            "confidence": round(best_score, 4)
        }

    return {
        "verified": False,
        "closest_score": round(best_score, 4)
    }
