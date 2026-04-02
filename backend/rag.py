import io
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

try:
    import PyPDF2
    _pypdf2_available = True
except ImportError:
    _pypdf2_available = False

_model = SentenceTransformer("all-MiniLM-L6-v2")

# In-memory store — resets on backend restart
_chunks: list[str] = []
_index: faiss.IndexFlatL2 | None = None

CHUNK_SIZE = 2000    # ~500 tokens at ~4 chars/token
CHUNK_OVERLAP = 200  # ~50 tokens


def _extract_text(file_bytes: bytes, filename: str) -> str:
    if filename.lower().endswith(".pdf"):
        if not _pypdf2_available:
            raise RuntimeError("PyPDF2 is not installed — cannot extract PDF text.")
        reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n\n".join(pages)
    # Plain text fallback
    return file_bytes.decode("utf-8", errors="replace")


def _chunk_text(text: str) -> list[str]:
    chunks = []
    start = 0
    while start < len(text):
        end = start + CHUNK_SIZE
        chunks.append(text[start:end])
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return [c.strip() for c in chunks if c.strip()]


def add_documents(file_bytes: bytes, filename: str) -> int:
    global _index

    text = _extract_text(file_bytes, filename)
    new_chunks = _chunk_text(text)
    if not new_chunks:
        return 0

    embeddings = _model.encode(new_chunks, normalize_embeddings=True).astype("float32")

    if _index is None:
        dim = embeddings.shape[1]
        _index = faiss.IndexFlatL2(dim)

    _index.add(embeddings)
    _chunks.extend(new_chunks)

    return len(new_chunks)


def retrieve(query: str, k: int = 3) -> list[str]:
    if _index is None or len(_chunks) == 0:
        return []

    query_vec = _model.encode([query], normalize_embeddings=True).astype("float32")
    k = min(k, len(_chunks))
    _, indices = _index.search(query_vec, k)

    return [_chunks[i] for i in indices[0] if i < len(_chunks)]
