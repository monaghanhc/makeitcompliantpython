"""Fast batch TF-IDF similarity against cached license templates."""

from __future__ import annotations

from dataclasses import dataclass

from sklearn.metrics.pairwise import cosine_similarity as sk_cosine

from makeitcompliant.app.ml.features import normalize_license_text, preprocess_tokens
from makeitcompliant.app.ml.model_cache import TemplateEntry, load_template_cache
from makeitcompliant.app.utils.logging_config import get_logger

logger = get_logger("ml.similarity")

_vectorizer = None
_template_matrix = None
_templates: tuple[TemplateEntry, ...] = ()


def _ensure_matrix() -> None:
    global _vectorizer, _template_matrix, _templates
    if _template_matrix is not None:
        return
    from sklearn.feature_extraction.text import TfidfVectorizer

    _templates = load_template_cache()
    if not _templates:
        raise RuntimeError("No license templates loaded for ML similarity.")
    texts = [normalize_license_text(t.text) for t in _templates]
    _vectorizer = TfidfVectorizer(
        use_idf=True,
        tokenizer=preprocess_tokens,
        stop_words="english",
    )
    _template_matrix = _vectorizer.fit_transform(texts)
    logger.info("Built TF-IDF matrix for %d templates", len(_templates))


@dataclass(frozen=True)
class TemplateScore:
    entry: TemplateEntry
    score: float


def rank_templates(text: str, top_n: int = 5) -> list[TemplateScore]:
    """Return top template matches by cosine similarity (single matrix multiply)."""
    _ensure_matrix()
    assert _vectorizer is not None and _template_matrix is not None
    normalized = normalize_license_text(text)
    if not normalized:
        return []
    query = _vectorizer.transform([normalized])
    scores = sk_cosine(query, _template_matrix).flatten()
    pairs = [
        TemplateScore(entry=_templates[i], score=float(scores[i]))
        for i in range(len(_templates))
    ]
    ranked = sorted(pairs, key=lambda s: s.score, reverse=True)
    return ranked[:top_n]


def best_template_score(text: str) -> TemplateScore | None:
    ranked = rank_templates(text, top_n=1)
    return ranked[0] if ranked else None
