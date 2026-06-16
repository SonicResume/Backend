from fastapi import FastAPI, UploadFile, File, Form, HTTPException
import modal
import concurrent.futures

from db import add_face, search_face, load_db

# -----------------------
# FASTAPI APP
# -----------------------
app = FastAPI()

# -----------------------
# MODAL SERVICE
# -----------------------
FaceService = modal.Cls.from_name("face-gpu", "FaceService")
face = FaceService()

# -----------------------
# INIT DB
# -----------------------
load_db()

# -----------------------
# OPTIONAL SYNC WRAPPER (fallback safety)
# -----------------------
def run_sync(func, data, timeout=120):
    with concurrent.futures.ThreadPoolExecutor() as ex:
        return ex.submit(func, data).result(timeout=timeout)

# -----------------------
# ROOT
# -----------------------
@app.get("/")
def root():
    return {"status": "ok"}

# -----------------------
# EMBED TEST
# -----------------------
@app.post("/embed")
async def embed(file: UploadFile = File(...)):

    try:
        img_bytes = await file.read()

        print("🔥 /embed hit")

        # ✅ ASYNC MODAL CALL (FIXED)
        result = await face.embed.remote.aio(img_bytes)

        return {
            "embedding": result,
            "dim": len(result) if result else 0
        }

    except Exception as e:
        print("❌ EMBED ERROR:", repr(e))
        raise HTTPException(status_code=500, detail=str(e))

# -----------------------
# REGISTER FACE
# -----------------------
@app.post("/register")
async def register(file: UploadFile = File(...), name: str = Form(...)):

    try:
        img = await file.read()

        print("🔥 REGISTER HIT")

        # ✅ ASYNC MODAL CALL
        emb = await face.embed.remote.aio(img)

        if isinstance(emb, dict):
            return {"error": "no_face_detected"}

        if not emb:
            return {"error": "empty_embedding"}

        add_face(emb, name)

        print("✅ SAVED TO DB")

        return {"status": "saved", "name": name}

    except Exception as e:
        print("❌ REGISTER ERROR:", repr(e))
        raise HTTPException(status_code=500, detail=str(e))

# -----------------------
# SEARCH FACE
# -----------------------
@app.post("/search")
async def search(file: UploadFile = File(...)):

    try:
        img = await file.read()

        print("🔎 SEARCH HIT")

        # ✅ ASYNC MODAL CALL
        emb = await face.embed.remote.aio(img)

        if isinstance(emb, dict):
            return {"error": "no_face"}

        results = search_face(emb)

        return {"matches": results}

    except Exception as e:
        print("❌ SEARCH ERROR:", repr(e))
        raise HTTPException(status_code=500, detail=str(e))
