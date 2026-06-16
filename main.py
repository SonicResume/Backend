from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from pathlib import Path
from contextlib import asynccontextmanager
from email.mime.text import MIMEText
from fastapi import UploadFile, File
from pathlib import Path
from fastapi.staticfiles import StaticFiles

import json
import uuid
import time
import asyncio
import httpx
import cv2
import numpy as np
import onnxruntime as ort
import edge_tts
import smtplib
import os
os.environ["ORT_LOG_LEVEL"] = "3"
import subprocess

from insightface.app import FaceAnalysis
from stream_engine import RealtimeFaceEngine
from vector_store import VectorStore
from pydantic import BaseModel

app = FastAPI()

MEDIA_DIR = Path("media")
MEDIA_DIR.mkdir(exist_ok=True)

VIDEO_DIR = Path("videos")
AUDIO_DIR = Path("audio")
OUTPUT_DIR = Path("outputs")

VIDEO_DIR.mkdir(exist_ok=True)
AUDIO_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

class VideoRequest(BaseModel):
    video_path: str
    audio_path: str

class AudioRequest(BaseModel):
    text: str
    voice: str = "en-US-JennyNeural"

# =========================
# WORKFLOW
# =========================

WORKFLOWS = {
    "flux": "workflow_flux.json",
    "juggernaut": "corperate_headshots.json",
    "dream": "anime_headshots.json",
    "anything": "anime_characters.json",
}
# =========================
# GPU PROVIDERS
# =========================
providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]

# =========================
# APP LIFESPAN (PRODUCTION)
# =========================
@asynccontextmanager
async def lifespan(app: FastAPI):
    face.prepare(ctx_id=0, det_size=(640, 640))
    print("[SYSTEM] Providers:", providers)
    print("[SYSTEM] GPU FACE ENGINE READY")
    yield
    print("[SYSTEM] SHUTDOWN COMPLETE")


app = FastAPI(lifespan=lifespan)

# =========================
# CORS
# =========================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =========================
# PATHS
# =========================
BASE_DIR = Path(__file__).parent
WORKFLOW_PATH = BASE_DIR / "workflow_flux.json"
IMAGES_DIR = BASE_DIR / "pictures" / "generated"
IMAGES_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/images", StaticFiles(directory=IMAGES_DIR), name="images")

COMFY_URL = "http://127.0.0.1:8188"

# =========================
# MEMORY
# =========================
TASKS = {}
IDENTITY_DB = {}

def send_email(to, subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = "your@email.com"
    msg["To"] = to

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login("your@email.com", "app_password")
        server.send_message(msg)

# =========================
# GPU FACE MODEL
# =========================
face = FaceAnalysis(
    name="buffalo_l",
    providers=["CUDAExecutionProvider", "CPUExecutionProvider"]
)

# =========================
# FAISS VECTOR DB
# =========================
vector_db = VectorStore(dim=512)

# =========================
# REALTIME ENGINE
# =========================
realtime = RealtimeFaceEngine(face, vector_db)

# =========================
# MODELS
# =========================
class GenerateImageRequest(BaseModel):
    prompt: str
    batch: int = 1
    width: int = 1024
    height: int = 1024

# =========================
# HELPERS
# =========================
def load_workflow():
    with open(WORKFLOW_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def normalize(v):
    v = np.array(v)
    return v / (np.linalg.norm(v) + 1e-8)

def get_embedding(image_path: str):
    img = cv2.imread(image_path)
    if img is None:
        return None

    faces = face.get(img)
    if not faces:
        return None

    return normalize(faces[0].embedding)

def find_identity(vec, threshold=0.45):
    best_id, best_score = None, -1.0

    for identity_id, saved in IDENTITY_DB.items():
        saved = np.array(saved)
        saved = saved / (np.linalg.norm(saved) + 1e-8)

        score = float(np.dot(vec, saved))
        if score > best_score:
            best_score = score
            best_id = identity_id

    if best_score >= threshold:
        return best_id, best_score

    return None, best_score

# =========================
# ROOT
# =========================
@app.get("/")
def root():
    return {"status": "GPU biometric service running"}

# =========================
# EMAIL SERVICE
# =========================
@app.post("/send-email")
async def send_email_api(to: str, subject: str, body: str):
    send_email(to, subject, body)
    return {"status": "sent"}

# =========================
# FACE UPLOAD
# =========================
@app.post("/upload-face")
async def upload_face(file: UploadFile = File(...)):

    content = await file.read()
    tmp = IMAGES_DIR / f"{uuid.uuid4().hex}.png"
    tmp.write_bytes(content)

    vec = get_embedding(str(tmp))
    if vec is None:
        raise HTTPException(400, "No face detected")

    existing, score = find_identity(vec)

    if existing:
        return {"identity_id": existing, "matched": True, "score": score}

    new_id = str(uuid.uuid4())
    IDENTITY_DB[new_id] = vec.tolist()

    # ALSO ADD TO FAISS
    vector_db.add(vec, new_id)

    return {"identity_id": new_id, "matched": False}

# =========================
# REALTIME STREAM
# =========================
@app.post("/stream/frame")
async def stream_frame(file: UploadFile = File(...)):
    img_bytes = await file.read()

    np_img = np.frombuffer(img_bytes, np.uint8)
    frame = cv2.imdecode(np_img, cv2.IMREAD_COLOR)

    if frame is None:
        raise HTTPException(400, "invalid frame")

    results = realtime.process_frame(frame)

    return {
        "faces": results,
        "count": len(results)
    }

# =========================
# IMAGE GENERATION (COMFYUI)
# =========================
@app.post("/generate-image")
async def generate(data: GenerateImageRequest):

    workflow = load_workflow("flux")

    workflow["2"]["inputs"]["text"] = data.prompt

    workflow["4"]["inputs"]["width"] = data.width
    workflow["4"]["inputs"]["height"] = data.height
    workflow["4"]["inputs"]["batch_size"] = data.batch

    workflow["5"]["inputs"]["seed"] = uuid.uuid4().int % 1_000_000_000

    # ✅ THIS IS WHERE OLD SYSTEM BELONGS
    identity_id = getattr(data, "identity_id", None)

    if identity_id and identity_id in IDENTITY_DB:
        workflow["2"]["inputs"]["text"] = (
            "identity lock: same person, consistent facial structure, "
            "preserve identity, do not change face, "
            + data.prompt
        )

    async with httpx.AsyncClient() as client:
        r = await client.post(
            f"{COMFY_URL}/prompt",
            json={"prompt": workflow}
        )

    return r.json()

# =========================
# AUDIO GENERATION
# =========================
from pydantic import BaseModel

class AudioRequest(BaseModel):
    text: str
    voice: str = "en-US-JennyNeural"
@app.post("/generate-audio")
async def generate_audio(data: AudioRequest):
    output_file = IMAGES_DIR / f"{uuid.uuid4().hex}.mp3"

    communicate = edge_tts.Communicate(data.text, data.voice)
    await communicate.save(str(output_file))

    return {
        "audio_url": f"/images/{output_file.name}",
        "text": data.text
    }
# =========================
# VIDEO GENERATION
# =========================

@app.post("/generate-video")
async def generate_video(data: GenerateImageRequest):
    workflow = load_workflow()

    # inject prompt
    workflow["2"]["inputs"]["text"] = data.prompt

    # video settings (make sure node IDs exist in your workflow JSON)
    workflow["10"]["inputs"]["fps"] = 24
    workflow["10"]["inputs"]["frames"] = 48

    async with httpx.AsyncClient(timeout=120) as client:
        r = await client.post(
            f"{COMFY_URL}/prompt",
            json={"prompt": workflow}
        )

        r.raise_for_status()
        response = r.json()

    prompt_id = response.get("prompt_id")

    return {
        "task_id": prompt_id,
        "type": "video"
    }

# =========================
# COMPOSE-VIDEO
# =========================

@app.post("/compose-video")
async def compose_video(
    image: UploadFile = File(...),
    audio: UploadFile = File(...)
):
    job_id = uuid.uuid4().hex

    img_path = MEDIA_DIR / f"{job_id}.png"
    audio_path = MEDIA_DIR / f"{job_id}.mp3"
    output_path = MEDIA_DIR / f"{job_id}.mp4"

    # save uploads
    with open(img_path, "wb") as f:
        f.write(await image.read())

    with open(audio_path, "wb") as f:
        f.write(await audio.read())

    # ffmpeg command (simple slideshow video)
    cmd = [
        "ffmpeg",
        "-y",
        "-loop", "1",
        "-i", str(img_path),
        "-i", str(audio_path),
        "-c:v", "libx264",
        "-tune", "stillimage",
        "-c:a", "aac",
        "-b:a", "192k",
        "-pix_fmt", "yuv420p",
        "-shortest",
        str(output_path)
    ]

    subprocess.run(cmd, check=True)

    return {
        "status": "done",
        "video_url": f"/media/{job_id}.mp4"
    }

# =========================
# TASK ID 
# =========================

@app.get("/task/{task_id}")
async def get_task(task_id: str):
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{COMFY_URL}/history/{task_id}")
        r.raise_for_status()
        return r.json()

# =========================
# MOUNT
# =========================

app.mount("/media", StaticFiles(directory="media"), name="media")

# =========================
# IMAGE TO VIDEO
# =========================

@app.post("/image-to-video")
async def image_to_video(image_url: str, audio_url: str):

    video_id = uuid.uuid4().hex
    output_path = IMAGES_DIR / f"{video_id}.mp4"

    cmd = [
        "ffmpeg",
        "-loop", "1",
        "-i", image_url,
        "-i", audio_url,
        "-c:v", "libx264",
        "-c:a", "aac",
        "-shortest",
        str(output_path)
    ]

    import subprocess
    subprocess.run(cmd)

    return {"video_url": f"/images/{output_path.name}"}

# =========================
# TEST SIGNAL
# =========================

@app.get("/")
def root():
    return {"status": "GPU biometric service running"}

# =========================
# BACKGROUND WORKER
# =========================
async def worker(prompt_id: str, batch: int):

    start = time.time()

    while True:
        if time.time() - start > 300:
            TASKS[prompt_id] = {"status": "failed", "images": []}
            return

        async with httpx.AsyncClient() as client:
            res = await client.get(f"{COMFY_URL}/history/{prompt_id}")
            history = res.json()

        data = history.get(prompt_id)
        if not data:
            await asyncio.sleep(1)
            continue

        outputs = data.get("outputs", {})
        images = []

        async with httpx.AsyncClient() as client:
            for node in outputs.values():
                for img in node.get("images", []):

                    url = (
                        f"{COMFY_URL}/view"
                        f"?filename={img['filename']}"
                        f"&subfolder={img['subfolder']}"
                        f"&type={img['type']}"
                    )

                    r = await client.get(url)

                    fname = f"{uuid.uuid4().hex}.png"
                    path = IMAGES_DIR / fname
                    path.write_bytes(r.content)

                    images.append(f"/images/{fname}")

        TASKS[prompt_id] = {
            "status": "done",
            "images": images[:batch]
        }
        return

# =========================
# TASK STATUS
# =========================
@app.get("/tasks/{task_id}")
def get_task(task_id: str):
    if task_id not in TASKS:
        raise HTTPException(404, "Not found")
    return TASKS[task_id]
