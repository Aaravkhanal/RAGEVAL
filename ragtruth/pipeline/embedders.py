"""Dense embedding wrappers with SentenceTransformers and normalization."""

from __future__ import annotations
from typing import List
import numpy as np
import torch
from sentence_transformers import SentenceTransformer
from ragtruth.core.config import EmbedderConfig


class SentenceTransformerEmbedder:
    """Wrapper around SentenceTransformer with MPS/CUDA/CPU device handling and L2 normalization."""

    def __init__(self, config: Optional[EmbedderConfig] = None):
        self.config = config or EmbedderConfig()
        
        # Auto-detect optimal device if requested device is cpu or auto
        device = self.config.device
        if device == "auto":
            if torch.cuda.is_available():
                device = "cuda"
            elif torch.backends.mps.is_available():
                device = "mps"
            else:
                device = "cpu"
        self.device = device
        
        self.model = SentenceTransformer(self.config.model_name, device=self.device)
        if hasattr(self.model, "get_embedding_dimension"):
            self.dimension = self.model.get_embedding_dimension()
        else:
            self.dimension = self.model.get_sentence_embedding_dimension()

    def encode(self, texts: List[str]) -> np.ndarray:
        if not texts:
            return np.empty((0, self.dimension), dtype=np.float32)

        embeddings = self.model.encode(
            texts,
            batch_size=self.config.batch_size,
            show_progress_bar=False,
            normalize_embeddings=self.config.normalize_embeddings,
            convert_to_numpy=True,
        )
        return embeddings.astype(np.float32)

    def encode_query(self, query: str) -> np.ndarray:
        return self.encode([query])[0]
