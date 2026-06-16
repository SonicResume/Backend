from fastapi import FastAPI, UploadFile, File, Form, HTTPException
import modal
import concurrent.futures
import uuid

from face_utils import get_embedding, find_identity
from pydantic import BaseModel

class GenerateImageRequest(BaseModel):
    prompt: str
    batch: int = 1
    identity_id: str | None = None

FACE_DB = {}
from face import get_embedding, find_identity
from vector_store import VectorStore
vector_db = VectorStore(dim=512)

from pathlib import Path
ImageGen = modal.Cls.from_name(
    "image-generator",
    "ImageGenerator"
)

image_gen = ImageGen()

from db import add_face, search_face, load_db
from fastapi.staticfiles import StaticFiles

IMAGES_DIR = Path("images")
IMAGES_DIR.mkdir(exist_ok=True)

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

@app.post("/generate-image")
async def generate(data: GenerateImageRequest):

    # -----------------------
    # GET FACE (if provided)
    # -----------------------
    face_image = None

    if getattr(data, "identity_id", None) and data.identity_id in FACE_DB:
        face_image = FACE_DB[data.identity_id].get("image")

    images = []

    # -----------------------
    # GENERATE IMAGES
    # -----------------------
    for _ in range(data.batch):

        img_bytes = await image_gen.generate_face.remote.aio(
            data.prompt,
            face_image
        )

        filename = f"{uuid.uuid4().hex}.png"
        path = IMAGES_DIR / filename
        path.write_bytes(img_bytes)

        images.append(f"/images/{filename}")

    return {"images": images}
# -----------------------
# APP MOUNT
# -----------------------
app.mount("/images", StaticFiles(directory="images"), name="images")

# -----------------------
# UPLOAD FACE
# -----------------------
@app.post("/upload-face")
async def upload_face(file: UploadFile = File(...)):

    content = await file.read()

    tmp_path = IMAGES_DIR / f"{uuid.uuid4().hex}.png"
    tmp_path.write_bytes(content)

    vec = get_embedding(str(tmp_path))
    if vec is None:
        raise HTTPException(400, "No face detected")

    # search existing face
    match_id, score = find_identity(vec)

    if match_id:
        return {"identity_id": match_id, "matched": True, "score": score}

    # create new id
    new_id = str(uuid.uuid4())

    FACE_DB[new_id] = {
        "embedding": vec,
        "image": str(tmp_path)
    }

    vector_db.add(vec, new_id)

    return {"identity_id": new_id, "matched": False}
