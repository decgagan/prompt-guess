"""Prompt Guess scoring engine: semantic similarity + keyword bonus -> 0-100."""
from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path

import numpy as np

from .keywords import keyword_match

MODEL_NAME = "BAAI/bge-small-en-v1.5"  # == @cf/baai/bge-small-en-v1.5 on Workers AI
PARAMS_PATH = Path(__file__).with_name("params.json")


@dataclass
class Params:
    cos_lo: float = 0.45   # cosine at/below which semantic score is 0
    cos_hi: float = 0.95   # cosine at/above which semantic score is 100
    gamma: float = 1.0     # curve shape for the semantic mapping
    kw_weight: float = 0.2 # share of the final score from keyword recall
    version: int = 1        # 1 = original synonym table, 2 = + v2 synonym groups
    thresholds: dict = field(default_factory=lambda: {"great": 80, "close": 55, "partial": 30})

    @classmethod
    def load(cls, path: Path = PARAMS_PATH, version: int | None = None) -> "Params":
        if version == 1:
            path = PARAMS_PATH.with_name("params_v1.json")
        return cls(**json.loads(path.read_text())) if path.exists() else cls()

    def save(self, path: Path = PARAMS_PATH) -> None:
        path.write_text(json.dumps(asdict(self), indent=2) + "\n")


def semantic_score(cos: float, p: Params) -> float:
    x = (cos - p.cos_lo) / (p.cos_hi - p.cos_lo)
    x = min(max(x, 0.0), 1.0)
    return 100.0 * x ** p.gamma


def combine(cos: float, kw_recall: float, p: Params) -> float:
    s = (1 - p.kw_weight) * semantic_score(cos, p) + p.kw_weight * 100.0 * kw_recall
    return round(min(max(s, 0.0), 100.0), 1)


def bucket(score: float, p: Params) -> str:
    t = p.thresholds
    if score >= t["great"]:
        return "great"
    if score >= t["close"]:
        return "close"
    if score >= t["partial"]:
        return "partial"
    return "miss"


class Scorer:
    def __init__(self, params: Params | None = None, model=None):
        self.params = params or Params.load()
        if model is None:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer(MODEL_NAME)
        self.model = model

    def embed(self, texts: list[str]) -> np.ndarray:
        return np.asarray(self.model.encode(texts, normalize_embeddings=True))

    def cosine(self, answer: str, guess: str) -> float:
        a, g = self.embed([answer, guess])
        return float(np.dot(a, g))

    def score(self, answer: str, guess: str) -> dict:
        if not guess.strip():
            return {"score": 0.0, "bucket": "miss", "matched": [], "cosine": 0.0}
        cos = self.cosine(answer, guess)
        recall, matched = keyword_match(answer, guess, self.params.version)
        s = combine(cos, recall, self.params)
        return {"score": s, "bucket": bucket(s, self.params), "matched": matched,
                "cosine": round(cos, 4), "keyword_recall": round(recall, 3)}
