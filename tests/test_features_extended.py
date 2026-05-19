from makeitcompliant.app.ml.features import cosine_similarity, jaccard_similarity, preprocess_tokens


def test_preprocess_tokens() -> None:
    tokens = preprocess_tokens("Permission is hereby granted.")
    assert tokens
    assert "permission" in tokens


def test_similarity_empty() -> None:
    assert cosine_similarity("", "hello") == 0.0
    assert jaccard_similarity("", "") == 0.0
