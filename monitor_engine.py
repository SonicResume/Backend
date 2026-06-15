import cv2
import numpy as np
import os
import time
from datetime import datetime
from insightface.app import FaceAnalysis
import security_db

# Create alerts folder for intruder evidence logs
os.makedirs("alerts", exist_ok=True)

# 1. Initialize the AI Face Mapping models offline
print("🧠 Loading local AI models... (This might take a moment on first boot)")
face_analyser = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
face_analyser.prepare(ctx_id=0, det_size=(640, 640))

# 2. Boot up the local database configuration
security_db.init_db()

def run_security_monitor():
    # Load all allowed occupants into system memory
    trusted_registry = security_db.load_trusted_faces()
    print(f"✅ Loaded {len(trusted_registry)} trusted faces from local memory.")
    
    # Open connection to your local USB webcam (0 is usually your default camera)
    camera = cv2.VideoCapture(0)
    if not camera.isOpened():
        print("❌ [ERROR] Could not access the webcam device.")
        return

    print("\n⚡ [ACTIVE] Offline Monitor Armed. Press 'q' inside the window to exit.")
    
    last_alert_time = 0
    ALERT_COOLDOWN = 10  # Seconds to wait before sounding another alarm sequence

    while True:
        ret, frame = camera.read()
        if not ret:
            break

        # Scan the current video frame for faces
        faces = face_analyser.get(frame)

        for face in faces:
            # Draw a bounding box around the detected face on screen
            bbox = face.bbox.astype(int)
            cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (0, 255, 0), 2)

            probe_vector = face.normed_embedding
            is_recognized = False
            matched_name = "UNAUTHORIZED ENTRY"
            highest_score = -1.0

            # Compute Cosine Distance calculation to find matches
            for trusted in trusted_registry:
                dot_prod = np.dot(probe_vector, trusted["embedding"])
                norm_a = np.linalg.norm(probe_vector)
                norm_b = np.linalg.norm(trusted["embedding"])
                similarity = dot_prod / (norm_a * norm_b)

                if similarity > highest_score:
                    highest_score = similarity
                    if similarity > 0.60:  # 0.60 is the industry confidence threshold
                        is_recognized = True
                        matched_name = trusted["label"]

            # Update the bounding box with the text label color codes
            text_color = (0, 255, 0) if is_recognized else (0, 0, 255) # Green vs Red
            cv2.putText(frame, f"{matched_name} ({highest_score:.2f})", 
                        (bbox[0], bbox[1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, text_color, 2)

            # 🚨 TRIGGER INTRUSION PROTOCOL IF AN UNKNOWN FACE IS DETECTED
            if not is_recognized and (time.time() - last_alert_time > ALERT_COOLDOWN):
                last_alert_time = time.time()
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                snapshot_path = f"alerts/INTRUDER_{timestamp}.jpg"
                
                # Save physical evidence frame directly to your offline hard drive
                cv2.imwrite(snapshot_path, frame)
                print(f"🚨 [WARNING] Unknown face detected! Evidence logged: {snapshot_path}")
                
                # Trigger a local computer beep audio alert sequence
                # For Windows users:
                if os.name == 'nt':
                    import winsound
                    winsound.Beep(2000, 1000) # Frequency: 2000Hz, Duration: 1 second
                else:
                    # For Mac/Linux users:
                    print('\a') 

        # Display the live secure console window locally
        cv2.imshow("SonicLegal Secure Offline Monitor Console", frame)

        # Drop loop lock if the operator presses 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    camera.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    run_security_monitor()
