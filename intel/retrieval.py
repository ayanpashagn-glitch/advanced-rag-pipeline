"""Exact cosine FAISS search, plus lexical ranking for explicit evidence-only mode."""
import re
import numpy as np
import faiss

STOP = set('a an the is are was were of in to for and or it its this that what which how does do can about me tell please document documents'.split())


def tokens(text):
    return set(re.findall(r'[a-z0-9]+', text.lower())) - STOP


def rank(chunks, question, vectors=None, query_vector=None, limit=8):
    if not chunks:
        return []
    words = tokens(question)
    lexical = [len(words & tokens(c['text'])) / max(1, len(words)) for c in chunks]
    if vectors is not None:
        matrix = np.asarray(vectors, dtype=np.float32)
        query = np.asarray([query_vector], dtype=np.float32)
        if matrix.ndim != 2 or query.shape[1:] != matrix.shape[1:] or not np.isfinite(matrix).all() or not np.isfinite(query).all():
            raise ValueError('Invalid or incompatible embeddings. Reindex the selected documents.')
        faiss.normalize_L2(matrix)
        faiss.normalize_L2(query)
        index = faiss.IndexFlatIP(matrix.shape[1])
        index.add(matrix)
        scores, indices = index.search(query, len(chunks))
        cosine = {int(i): float(s) for i, s in zip(indices[0], scores[0])}
        # Hybrid retrieval gives exact requirement/heading terms meaningful weight while
        # retaining semantic recall for paraphrased questions.
        values = [0.70 * cosine[i] + 0.30 * lexical[i] for i in range(len(chunks))]
    else:
        values = lexical
    ordering = sorted(range(len(chunks)), key=lambda i: (-values[i], chunks[i]['id']))[:limit]
    return [chunks[i] | {'score': round(values[i], 4)} for i in ordering if values[i] > 0]
