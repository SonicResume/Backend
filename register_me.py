import cv2
import numpy as np
import time
from insightface.app import FaceAnalysis
import security_db

security_db.init_db()
print("🧠 Initializing local biometric mapping engine...")
face_analyser = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
face_analyser.prepare(ctx_id=0, det_size=(640, 640))

def capture_and_register():
    print("\n📷 Opening webcam preview...")
    print("Look directly into the camera. Capturing in 3 seconds...")
    camera = cv2.VideoCapture(0)
    if not camera.isOpened():
        print("❌ [ERROR] Could not access the webcam device.")
        return
    for countdown in range(3, 0, -1):
        print(f"{countdown}...")
        time.sleep(1)
    ret, frame = camera.read()
    camera.release()
    if not ret:
        print("❌ [ERROR] Failed to capture video frame.")
        return
    faces = face_analyser.get(frame)
    if not faces:
        print("❌ [ERROR] No face detected. Check room lighting and try again.")
        return
    security_db.register_trusted_face("Admin-User", faces.normed_embedding)
    print("\n✅ Success! Face vector securely saved inside 'trusted_vault.db'.")

if __name__ == "__main__":
    capture_and_register()
