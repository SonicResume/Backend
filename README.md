Good — a clean README is what turns this from “working backend” into “real product.”

Here’s a **ready-to-use README.md** tailored to your exact stack:

---

# 🚀 AI Backend (Face + Image + Audio + Video API)

A GPU-accelerated FastAPI backend for:

* 👤 Face recognition (InsightFace + FAISS)
* 🎨 Image generation (ComfyUI workflow)
* 🔊 Text-to-speech (Edge TTS)
* 🎬 Video generation pipeline
* 📡 Real-time frame processing
* 🧠 Identity matching system

---

## ⚙️ Tech Stack

* FastAPI
* ONNX Runtime (CUDA / CPU fallback)
* InsightFace
* FAISS vector database
* OpenCV
* Edge-TTS
* FFmpeg
* httpx async workers

---

## 📦 Installation

```bash
git clone https://github.com/yourname/ai-backend.git
cd ai-backend

python -m venv venv
source venv/bin/activate

pip install -r requirements.txt
```

---

## 🚀 Run Server

```bash
uvicorn main:app --reload --port 8000
```

API will be available at:

```
http://127.0.0.1:8000
```

Swagger UI:

```
http://127.0.0.1:8000/docs
```

---

## 🧠 Features

### 👤 Face Upload & Recognition

Upload a face image and get identity match or create new identity.

```http
POST /upload-face
```

---

### 📡 Real-Time Frame Processing

```http
POST /stream/frame
```

Returns detected faces per frame.

---

### 🎨 Image Generation (ComfyUI)

```http
POST /generate-image
```

```json
{
  "prompt": "a futuristic cyberpunk city",
  "batch": 1,
  "width": 1024,
  "height": 1024
}
```

---

### 🔊 Text to Speech

```http
POST /generate-audio
```

```json
{
  "text": "Hello world",
  "voice": "en-US-JennyNeural"
}
```

Returns:

```json
{
  "audio_url": "/images/file.mp3"
}
```

---

### 🎬 Video Generation

```http
POST /generate-video
```

---

### 🖼 Image → Video

```http
POST /image-to-video
```

---

### 📊 Task Status

```http
GET /tasks/{task_id}
```

---

## 🧠 Architecture

```
FastAPI
 ├── InsightFace (GPU face embeddings)
 ├── FAISS (vector identity DB)
 ├── ComfyUI (image generation)
 ├── Edge-TTS (audio generation)
 ├── FFmpeg (video pipeline)
 └── Async worker system
```

---

## ⚡ GPU Support

Automatically uses:

* CUDAExecutionProvider (preferred)
* CPU fallback (if CUDA missing)

Check:

```bash
python -c "import onnxruntime as ort; print(ort.get_available_providers())"
```

---

## 📁 Project Structure

```
backend/
 ├── main.py
 ├── vector_store.py
 ├── stream_engine.py
 ├── engine/
 ├── config/
 ├── routes/
 ├── services/
 ├── pictures/generated/
 └── workflow_flux.json
```

---

## 🧠 Notes

* Uses in-memory identity DB (upgradeable to Redis/Postgres)
* ComfyUI must be running at `127.0.0.1:8188`
* CUDA optional but recommended

