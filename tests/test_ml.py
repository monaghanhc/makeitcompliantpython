from pathlib import Path

import pytest

from makeitcompliant.app.core.license_models import normalize_template_name_to_prolog
from makeitcompliant.app.ml.classifier import LicenseClassifier
from makeitcompliant.app.ml.features import cosine_similarity, jaccard_similarity
from makeitcompliant.app.ml.similarity import best_template_score, rank_templates
from makeitcompliant.app.prolog.facts_loader import write_runtime_facts
from makeitcompliant.app.utils.paths import get_resource_root


def test_normalize_cern_licence_spelling() -> None:
    name = normalize_template_name_to_prolog(
        "CERN Open Hardware Licence Version 2 - Permissive.txt"
    )
    assert "License" in name
    assert "Licence" not in name


def test_cosine_identical_text() -> None:
    text = "Permission is hereby granted, free of charge."
    assert cosine_similarity(text, text) == pytest.approx(1.0, abs=1e-6)


def test_jaccard_identical_text() -> None:
    text = "alpha beta gamma"
    assert jaccard_similarity(text, text) == pytest.approx(1.0)


def test_batch_tfidf_ranks_mit_high() -> None:
    mit_path = get_resource_root() / "MIT-License.txt"
    if not mit_path.is_file():
        pytest.skip("MIT-License.txt not in repo root")
    text = mit_path.read_text(encoding="utf-8")
    best = best_template_score(text)
    assert best is not None
    assert best.score > 0.5
    top = rank_templates(text, top_n=3)
    assert len(top) >= 1
    assert top[0].score >= best.score


def test_classify_mit_license_sample() -> None:
    mit_path = get_resource_root() / "MIT-License.txt"
    if not mit_path.is_file():
        pytest.skip("MIT-License.txt not in repo root")
    text = mit_path.read_text(encoding="utf-8")
    match = LicenseClassifier().match(text)
    assert "MIT" in match.prolog_license_name
    assert match.confidence > 0.5


def test_write_runtime_facts_single_license(tmp_path: Path) -> None:
    out = write_runtime_facts("MIT License", output_path=tmp_path / "facts.pl")
    content = out.read_text(encoding="utf-8")
    assert content.count("can_use_commercially") >= 1
    assert 'license_a("MIT License").' in content
    assert 'license_b("' not in content
    assert content.count("%Commercial Use") == 1


def test_write_runtime_facts_pair_no_duplicate_base(tmp_path: Path) -> None:
    base = get_resource_root() / "allLicenseFactsBaseCopy.pl"
    out = tmp_path / "facts.pl"
    write_runtime_facts(
        "MIT License",
        "Apache License 2.0",
        base_path=base,
        output_path=out,
    )
    content = out.read_text(encoding="utf-8")
    assert content.count("%Commercial Use") == 1
    assert 'license_a("MIT License").' in content
    assert 'license_b("Apache License 2.0").' in content
