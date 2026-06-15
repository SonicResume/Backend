import sqlite3
import numpy as np

DB_FILE = "trusted_vault.db"

def init_db():
    """Initializes the offline database structure."""
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS trusted_faces (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                label TEXT UNIQUE NOT NULL,
                embedding BLOB NOT NULL
            )
        """)
        conn.commit()

def register_trusted_face(label: str, embedding: np.ndarray):
    """Saves a trusted facial vector structure locally."""
    embedding_bytes = embedding.astype(np.float32).tobytes()
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO trusted_faces (label, embedding) VALUES (?, ?)",
            (label, embedding_bytes)
        )
        conn.commit()
    print(f"🔒 [SUCCESS] Registered '{label}' into the secure offline vault.")

def load_trusted_faces():
    """Retrieves all trusted profiles for physical scanning matches."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT label, embedding FROM trusted_faces")
        rows = cursor.fetchall()
        
    profiles = []
    for label, embedding_bytes in rows:
        embedding = np.frombuffer(embedding_bytes, dtype=np.float32)
        profiles.append({"label": label, "embedding": embedding})
    return profiles
