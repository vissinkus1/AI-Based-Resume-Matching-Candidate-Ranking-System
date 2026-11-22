"""
services/embedding_service.py — Sentence-Transformers Embedding Service.

Provides:
  - Lazy singleton for SentenceTransformer('all-MiniLM-L6-v2')
  - In-memory SHA-1 caching of embeddings to prevent redundant encoding
  - Batch encoding with L2 normalization (dot product == cosine similarity)
  - Cosine similarity and pairwise matrix calculations
  - Linear cosine calibration from [low, high] to [0, 100] scale
"""

import hashlib
import logging
from typing import Any
import numpy as np

from app.core.scoring_config import SCORING

logger = logging.getLogger(__name__)


def calibrate_cosine(
    raw_cos: float,
    low: float = SCORING.semantic_raw_cos_low,
    high: float = SCORING.semantic_raw_cos_high,
) -> float:
    """
    Linearly rescale raw cosine similarity from [low, high] into a 0–100 score.

    Values at or below `low` become 0.0.
    Values at or above `high` become 100.0.
    """
    if high <= low:
        return 100.0 if raw_cos >= high else 0.0
    scaled = ((raw_cos - low) / (high - low)) * 100.0
    return max(0.0, min(100.0, float(scaled)))


class EmbeddingService:
    """
    In-memory embedding service with lazy model loading and SHA-1 caching.
    """

    def __init__(self, model_name: str = SCORING.embedding_model):
        self.model_name = model_name
        self._model: Any = None
        self._cache: dict[str, np.ndarray] = {}

    def _get_model(self):
        """Lazy load the sentence transformer model."""
        if self._model is None:
            try:
                import os
                os.environ.setdefault("HF_HUB_DISABLE_SYMLINKS_WARNING", "1")
                from sentence_transformers import SentenceTransformer
                logger.info("Loading sentence transformer model '%s'...", self.model_name)
                try:
                    self._model = SentenceTransformer(self.model_name, local_files_only=True)
                except Exception:
                    self._model = SentenceTransformer(self.model_name)
            except Exception as e:
                raise RuntimeError(
                    f"SentenceTransformer model '{self.model_name}' could not be loaded. "
                    f"Ensure sentence-transformers is installed and model files are accessible. "
                    f"Underlying error: {str(e)}"
                ) from e
        return self._model

    def embed(self, texts: list[str]) -> np.ndarray:
        """
        Embed a list of strings and return L2-normalized vectors (shape: N, D).

        Utilizes an in-memory SHA-1 cache so repeated texts (e.g. skills,
        common JD duties) are never encoded twice.
        """
        if not texts:
            return np.empty((0, 384), dtype=np.float32)

        results: list[np.ndarray | None] = [None] * len(texts)
        missing_indices: list[int] = []
        missing_texts: list[str] = []

        for idx, text in enumerate(texts):
            clean_text = text.strip() if text else ""
            h = hashlib.sha1(clean_text.encode("utf-8")).hexdigest()
            if h in self._cache:
                results[idx] = self._cache[h]
            else:
                missing_indices.append(idx)
                missing_texts.append(clean_text if clean_text else " ")

        if missing_texts:
            model = self._get_model()
            # Encode in batches with L2 normalization enabled
            encoded = model.encode(
                missing_texts,
                batch_size=32,
                show_progress_bar=False,
                normalize_embeddings=True,
                convert_to_numpy=True,
            )

            for i, emb in zip(missing_indices, encoded):
                clean_text = texts[i].strip() if texts[i] else ""
                h = hashlib.sha1(clean_text.encode("utf-8")).hexdigest()
                self._cache[h] = emb
                results[i] = emb

        return np.vstack([r for r in results if r is not None])

    def embed_single(self, text: str) -> np.ndarray:
        """Embed a single text string and return a 1D vector (shape: D,)."""
        return self.embed([text])[0]

    def cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Compute cosine similarity between two 1D or 2D unit-normalized vectors."""
        v1 = vec1.flatten()
        v2 = vec2.flatten()
        n1 = np.linalg.norm(v1)
        n2 = np.linalg.norm(v2)
        if n1 < 1e-9 or n2 < 1e-9:
            return 0.0
        # If already normalized, dot product == cosine
        return float(np.dot(v1 / n1, v2 / n2))

    def cosine_matrix(self, matrix1: np.ndarray, matrix2: np.ndarray) -> np.ndarray:
        """
        Compute pairwise cosine similarities between matrix1 (N, D) and matrix2 (M, D).
        Returns matrix of shape (N, M).
        """
        if matrix1.size == 0 or matrix2.size == 0:
            return np.empty((matrix1.shape[0], matrix2.shape[0]), dtype=np.float32)

        # Normalize rows safely
        norm1 = np.linalg.norm(matrix1, axis=1, keepdims=True)
        norm2 = np.linalg.norm(matrix2, axis=1, keepdims=True)
        norm1[norm1 < 1e-9] = 1.0
        norm2[norm2 < 1e-9] = 1.0

        n_matrix1 = matrix1 / norm1
        n_matrix2 = matrix2 / norm2

        return np.matmul(n_matrix1, n_matrix2.T)

    def cache_size(self) -> int:
        """Return number of cached embedding vectors."""
        return len(self._cache)

    def clear_cache(self) -> None:
        """Clear in-memory embedding cache."""
        self._cache.clear()


# Global singleton instance
_embedding_service_instance: EmbeddingService | None = None


def get_embedding_service() -> EmbeddingService:
    """Return the global EmbeddingService singleton."""
    global _embedding_service_instance
    if _embedding_service_instance is None:
        _embedding_service_instance = EmbeddingService()
    return _embedding_service_instance
