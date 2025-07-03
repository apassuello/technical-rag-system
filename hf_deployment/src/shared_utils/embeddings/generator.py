import numpy as np
import torch
from typing import List, Optional
from sentence_transformers import SentenceTransformer

# Global cache for embeddings
_embedding_cache = {}
_model_cache = {}


def generate_embeddings(
    texts: List[str],
    model_name: str = "sentence-transformers/multi-qa-MiniLM-L6-cos-v1",
    batch_size: int = 32,
    use_mps: bool = True,
) -> np.ndarray:
    """
    Generate embeddings for text chunks with caching.

    Args:
        texts: List of text chunks to embed
        model_name: SentenceTransformer model identifier
        batch_size: Processing batch size
        use_mps: Use Apple Silicon acceleration

    Returns:
        numpy array of shape (len(texts), embedding_dim)

    Performance Target:
        - 100 texts/second on M4-Pro
        - 384-dimensional embeddings
        - Memory usage <500MB
    """
    # Check cache for all texts
    cache_keys = [f"{model_name}:{text}" for text in texts]
    cached_embeddings = []
    texts_to_compute = []
    compute_indices = []
    
    for i, key in enumerate(cache_keys):
        if key in _embedding_cache:
            cached_embeddings.append((i, _embedding_cache[key]))
        else:
            texts_to_compute.append(texts[i])
            compute_indices.append(i)
    
    # Load model if needed
    if model_name not in _model_cache:
        model = SentenceTransformer(model_name)
        device = 'mps' if use_mps and torch.backends.mps.is_available() else 'cpu'
        model = model.to(device)
        model.eval()
        _model_cache[model_name] = model
    else:
        model = _model_cache[model_name]
    
    # Compute new embeddings
    if texts_to_compute:
        with torch.no_grad():
            new_embeddings = model.encode(
                texts_to_compute,
                batch_size=batch_size,
                convert_to_numpy=True,
                normalize_embeddings=False
            ).astype(np.float32)
        
        # Cache new embeddings
        for i, text in enumerate(texts_to_compute):
            key = f"{model_name}:{text}"
            _embedding_cache[key] = new_embeddings[i]
    
    # Reconstruct full embedding array
    result = np.zeros((len(texts), 384), dtype=np.float32)
    
    # Fill cached embeddings
    for idx, embedding in cached_embeddings:
        result[idx] = embedding
    
    # Fill newly computed embeddings
    if texts_to_compute:
        for i, original_idx in enumerate(compute_indices):
            result[original_idx] = new_embeddings[i]
    
    return result
