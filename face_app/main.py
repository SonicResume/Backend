from fastapi import FastAPI, UploadFile, File
import numpy as np
import cv2
import pickle

from db.database import init_db, get_conn
from utils.face import get_embedding

app = FastAPI()

init_db()


def cosine(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))


@app.post("/register")
async def register(user_id: str, file: UploadFile = File(...)):
    img_bytes = await file.read()
    npimg = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)

    emb = get_embedding(img)

    if emb is None:
        return {"error": "No face detected"}

    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO faces (user_id, embedding) VALUES (?, ?)",
        (user_id, pickle.dumps(emb))
    )

    conn.commit()
    conn.close()

    return {"status": "registered", "user_id": user_id}


@app.post("/check-in")
async def check_in(file: UploadFile = File(...)):
    img_bytes = await file.read()
    npimg = np.frombuffer(img_bytes, np.uint8)
    img = cv2.imdecode(npimg, cv2.IMREAD_COLOR)

    emb = get_embedding(img)

    if emb is None:
        return {"error": "No face detected"}

    conn = get_conn()
    cur = conn.cursor()

    cur.execute("SELECT user_id, embedding FROM faces")
    rows = cur.fetchall()

    best_user = None
    best_score = 0

    for user_id, db_emb in rows:
        stored = pickle.loads(db_emb)
        score = cosine(emb, stored)

        if score > best_score:
            best_score = score
            best_user = user_id

    if best_score < 0.35:
        return {"status": "unknown face"}

    cur.execute(
        "INSERT INTO attendance (user_id) VALUES (?)",
        (best_user,)
    )

    conn.commit()
    conn.close()

    return {
        "status": "present",
        "user_id": best_user,
        "confidence": float(best_score)
    }
