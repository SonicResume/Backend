import sqlite3
import numpy as np
import threading

DB_FILE = "face_vault.db"

# Thread-safe connection lock (important for FastAPI)
lock = threading.Lock()


# =========================
# INIT DB
# =========================
def init_db():
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS face_registry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                embedding BLOB NOT NULL
            )
        """)
        conn.commit()


# =========================
# NORMALIZE EMBEDDING
# =========================
def _normalize(vec: np.ndarray):
    vec = vec.astype(np.float32)
    return vec / (np.linalg.norm(vec) + 1e-8)


# =========================
# REGISTER FACE
# =========================
def register_face_vector(user_id: str, name: str, embedding: np.ndarray):
    embedding = _normalize(embedding)
    embedding_bytes = embedding.tobytes()

    with lock:
        with sqlite3.connect(DB_FILE) as conn:
            conn.execute(
                """
                INSERT INTO face_registry (user_id, name, embedding)
                VALUES (?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    name=excluded.name,
                    embedding=excluded.embedding
                """,
                (user_id, name, embedding_bytes)
            )
            conn.commit()


# =========================
# GET ALL FACES
# =========================
def get_all_registered_faces():
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, name, embedding FROM face_registry")
        rows = cursor.fetchall()

    faces = []
    for user_id, name, embedding_bytes in rows:
        try:
            embedding = np.frombuffer(embedding_bytes, dtype=np.float32)

            if embedding.size == 0:
                continue

            faces.append({
                "user_id": user_id,
                "name": name,
                "embedding": embedding
            })

        except Exception:
            continue

    return faces
