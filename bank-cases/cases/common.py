"""Общие примитивы: детерминированные эмбеддинги вместо внешней модели ИИ."""

from __future__ import annotations

import hashlib
import math


def embed(text: str, size: int = 64) -> list[float]:
    """Детерминированный вектор текста — офлайн-замена вызова модели эмбеддингов."""
    digest = hashlib.sha256(text.lower().strip().encode()).digest()
    return [digest[index % len(digest)] / 255 for index in range(size)]


def cosine(left: str, right: str) -> float:
    return round(_cosine(embed(left), embed(right)), 4)


def _cosine(left: list[float], right: list[float]) -> float:
    norm = math.sqrt(sum(a * a for a in left) * sum(b * b for b in right)) or 1.0
    return sum(a * b for a, b in zip(left, right, strict=True)) / norm


PUNCT = ".,;:!?()«»\"'—–-/"


def _stem(raw: str) -> str:
    return raw.strip(PUNCT).lower()[:4]


def keywords(text: str) -> set[str]:
    return {_stem(word) for word in text.split() if len(word.strip(PUNCT)) > 3}
