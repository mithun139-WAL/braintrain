import logging
import hashlib
import numpy as np
import httpx
from typing import List
from app.core.config import get_settings

logger = logging.getLogger("memory_encoder")

class MemoryEncoder:
    def __init__(self):
        self.settings = get_settings()
        self.dim = 1536  # Default dimension matching OpenAI / NIM standard

    async def encode(self, text: str) -> List[float]:
        """
        Encodes a string into a 1536-dimensional float vector.
        Tries Free HF API, falls back to NVIDIA NIM, and finally to local deterministic hashing.
        """
        if not text or not text.strip():
            return [0.0] * self.dim

        # 1. Try Free Hugging Face Inference API (using BAAI/bge-large-en-v1.5 or all-MiniLM-L6-v2)
        # To match the 1536 dimension, we pad or truncate the vector.
        try:
            async with httpx.AsyncClient() as client:
                # BAAI/bge-large-en-v1.5 outputs 1024 dimensions
                response = await client.post(
                    "https://api-inference.huggingface.co/pipeline/feature-extraction/BAAI/bge-large-en-v1.5",
                    json={"inputs": text},
                    timeout=5.0
                )
                if response.status_code == 200:
                    vec = response.json()
                    if isinstance(vec, list) and len(vec) > 0:
                        # If nested list, extract first item
                        if isinstance(vec[0], list):
                            vec = vec[0]
                        # Pad/truncate to 1536
                        return self._pad_or_truncate(vec, self.dim)
        except Exception as e:
            logger.debug("Free Hugging Face API failed, trying NVIDIA NIM: %s", e)

        # 2. Try NVIDIA NIM Embeddings API
        if self.settings.nvidia_api_key:
            try:
                url = f"{self.settings.nvidia_base_url}/embeddings"
                headers = {
                    "Authorization": f"Bearer {self.settings.nvidia_api_key}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "input": [text],
                    "model": "nvidia/embed-qa-4",  # or nomic-embed-text
                    "encoding_format": "float"
                }
                async with httpx.AsyncClient() as client:
                    response = await client.post(url, headers=headers, json=payload, timeout=5.0)
                    if response.status_code == 200:
                        res_json = response.json()
                        vec = res_json["data"][0]["embedding"]
                        return self._pad_or_truncate(vec, self.dim)
            except Exception as e:
                logger.error("NVIDIA NIM embedding encoding failed: %s", e)

        # 3. Deterministic Hashing Fallback (Offline / Fail-safe)
        logger.warning("Using deterministic hash-based fallback embedding for text: '%s'", text[:30])
        return self._generate_hash_embedding(text)

    def _pad_or_truncate(self, vec: List[float], target_dim: int) -> List[float]:
        current_len = len(vec)
        if current_len == target_dim:
            return vec
        elif current_len > target_dim:
            return vec[:target_dim]
        else:
            return vec + [0.0] * (target_dim - current_len)

    def _generate_hash_embedding(self, text: str) -> List[float]:
        """
        Generates a deterministic 1536-dimensional unit vector using md5 hashing of chunks
        of the input text. Guaranteed to yield the same vector for the same string.
        """
        vector = []
        # Hash sliding chunks of text to fill up 1536 dimensions (96 hashes * 16 bytes = 1536 floats)
        for i in range(96):
            h = hashlib.md5(f"{text}_{i}".encode("utf-8")).digest()
            # Convert 16 bytes into 16 floats normalized in range [-1.0, 1.0]
            for byte in h:
                vector.append((byte / 127.5) - 1.0)
        
        # Normalize to unit length (L2 norm)
        arr = np.array(vector)
        norm = np.linalg.norm(arr)
        if norm > 0:
            arr = arr / norm
        return arr.tolist()
