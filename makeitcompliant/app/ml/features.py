"""Text normalization and similarity metrics (offline, lightweight)."""

from __future__ import annotations

import re
import string
from functools import lru_cache

import nltk
from sklearn.feature_extraction.text import TfidfVectorizer

from makeitcompliant.app.utils.logging_config import get_logger

logger = get_logger("ml.features")

_PUNCT_TABLE = str.maketrans("", "", string.punctuation)
_WHITESPACE_RE = re.compile(r"\s+")


def _ensure_nltk_punkt() -> None:
    for resource in ("punkt", "punkt_tab"):
        try:
            nltk.data.find(f"tokenizers/{resource}")
        except LookupError:
            logger.info("Downloading NLTK resource %s (one-time).", resource)
            nltk.download(resource, quiet=True)


def normalize_license_text(text: str) -> str:
    """Collapse whitespace for stable comparison."""
    return _WHITESPACE_RE.sub(" ", text.strip())


def preprocess_tokens(text: str) -> list[str]:
    _ensure_nltk_punkt()
    lowered = text.lower().translate(_PUNCT_TABLE)
    return nltk.word_tokenize(lowered)


@lru_cache(maxsize=1)
def _vectorizer() -> TfidfVectorizer:
    return TfidfVectorizer(use_idf=True, tokenizer=preprocess_tokens, stop_words="english")


def cosine_similarity(text_a: str, text_b: str) -> float:
    a = normalize_license_text(text_a)
    b = normalize_license_text(text_b)
    if not a or not b:
        return 0.0
    tfidf = _vectorizer().fit_transform([a, b])
    return float(((tfidf * tfidf.T).toarray())[0, 1])


def jaccard_similarity(text_a: str, text_b: str) -> float:
    set_a = set(normalize_license_text(text_a).split())
    set_b = set(normalize_license_text(text_b).split())
    if not set_a or not set_b:
        return 0.0
    intersection = set_a & set_b
    union_size = len(set_a) + len(set_b) - len(intersection)
    return float(len(intersection) / union_size) if union_size else 0.0
