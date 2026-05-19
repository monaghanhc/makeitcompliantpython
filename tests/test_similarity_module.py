from makeitcompliant.app.ml import similarity as sim


def test_rank_empty_text() -> None:
    assert sim.rank_templates("   ") == []


def test_ensure_matrix_cached(mit_text: str) -> None:
    sim._vectorizer = None
    sim._template_matrix = None
    best = sim.best_template_score(mit_text)
    assert best is not None
    second = sim.best_template_score(mit_text)
    assert second is not None
    assert second.score == best.score
