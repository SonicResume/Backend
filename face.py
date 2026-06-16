from deepface import DeepFace

def verify_faces(img1_path, img2_path):
    return DeepFace.verify(img1_path, img2_path)

def get_embedding(img_path):
    return DeepFace.represent(img_path, model_name="Facenet")

def find_identity(vec):
    # placeholder for now (your vector DB can go here)
    return None, 0.0
