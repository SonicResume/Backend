import faiss
import numpy as np

class VectorStore:
    def __init__(self, dim=512):
        self.dim = dim
        self.index = faiss.IndexFlatIP(dim)  # cosine similarity (after normalization)
        self.ids = []

    def add(self, embedding, user_id):
        embedding = np.array(embedding).astype("float32")
        embedding = embedding / np.linalg.norm(embedding)

        self.index.add(np.array([embedding]))
        self.ids.append(user_id)

    def search(self, embedding, top_k=1):
        embedding = np.array(embedding).astype("float32")
        embedding = embedding / np.linalg.norm(embedding)

        scores, indices = self.index.search(np.array([embedding]), top_k)

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx != -1:
                results.append((self.ids[idx], float(score)))

        return results
