"""Eel local web UI (legacy; full Prolog analysis requires desktop app)."""

from __future__ import annotations

import sys
from dataclasses import dataclass

import eel

from makeitcompliant.app.ml.classifier import LicenseClassifier
from makeitcompliant.app.ml.features import cosine_similarity, jaccard_similarity
from makeitcompliant.app.utils.logging_config import setup_logging
from makeitcompliant.app.utils.paths import get_web_dir


@dataclass
class CompareResult:
    name: str
    value: str


@eel.expose
def compare(sent_files: list[dict]) -> list[dict]:
    a, b = sent_files[0]["data"], sent_files[1]["data"]
    return [
        CompareResult("Cosine Similarity: ", f"{cosine_similarity(a, b) * 100:.2f}").__dict__,
        CompareResult("Jaccard Similarity: ", f"{jaccard_similarity(a, b) * 100:.2f}").__dict__,
    ]


@eel.expose
def classify(sent_file: dict) -> list[dict]:
    classifier = LicenseClassifier()
    match = classifier.match(sent_file["data"], min_confidence=0.95)
    return [
        {
            "name": match.template_filename,
            "value": str(match.confidence),
        }
    ]


def main() -> None:
    setup_logging()
    web_dir = get_web_dir()
    if not web_dir.is_dir():
        raise FileNotFoundError(f"Web assets not found: {web_dir}")
    eel.init(str(web_dir))
    eel.start("upload.html", mode="None")


if __name__ == "__main__":
    main()
    sys.exit(0)
