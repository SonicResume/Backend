import uuid
import subprocess
from pathlib import Path

OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

def merge_video_audio(video_path, audio_path):
    output = OUTPUT_DIR / f"{uuid.uuid4().hex}.mp4"

    cmd = [
        "ffmpeg",
        "-y",
        "-i", str(video_path),
        "-i", str(audio_path),
        "-c:v", "libx264",
        "-c:a", "aac",
        "-shortest",
        str(output)
    ]

    subprocess.run(cmd, check=True)
    return str(output)
