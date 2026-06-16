import faiss
import numpy as np
import os
import json

DIM = 512

index = faiss.IndexFlatL2(DIM)

names = []

DB_PATH = "faces.index"
META_PATH = "faces.json"


def load_db():
    global names, index

    if os.path.exists(DB_PATH):
        index = faiss.read_index(DB_PATH)

    if os.path.exists(META_PATH):
        with open(META_PATH, "r") as f:
            names = json.load(f)


def save_db():
    faiss.write_index(index, DB_PATH)

    with open(META_PATH, "w") as f:
        json.dump(names, f)


def add_face(vector, name):
    v = np.array([vector]).astype("float32")
    index.add(v)
    names.append(name)
    save_db()


def search_face(vector, k=1):
    v = np.array([vector]).astype("float32")
    D, I = index.search(v, k)

    results = []
    for idx, dist in zip(I[0], D[0]):
        if idx < len(names):
            results.append({
                "name": names[idx],
                "distance": float(dist)
            })

    return results
