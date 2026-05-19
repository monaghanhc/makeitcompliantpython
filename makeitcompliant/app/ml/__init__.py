from makeitcompliant.app.ml.classifier import LicenseClassifier, MatchResult
from makeitcompliant.app.ml.features import (
    cosine_similarity,
    jaccard_similarity,
    normalize_license_text,
)

__all__ = [
    "LicenseClassifier",
    "MatchResult",
    "cosine_similarity",
    "jaccard_similarity",
    "normalize_license_text",
]
