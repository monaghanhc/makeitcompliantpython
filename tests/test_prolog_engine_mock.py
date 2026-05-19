from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from makeitcompliant.app.prolog.engine import PrologEngine, PrologEngineError


def test_query_missing_kb(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "makeitcompliant.app.prolog.engine.get_prolog_runtime_kb_path",
        lambda: tmp_path / "missing.pl",
    )
    engine = PrologEngine()
    with pytest.raises(PrologEngineError, match="Runtime Prolog KB missing"):
        engine.query("true")


def test_query_success(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    kb = tmp_path / "facts.pl"
    kb.write_text("% facts\n", encoding="utf-8")
    monkeypatch.setattr(
        "makeitcompliant.app.prolog.engine.get_prolog_runtime_kb_path",
        lambda: kb,
    )
    thread = MagicMock()
    thread.query.return_value = [{"X": "mit"}]
    mqi = MagicMock()
    mqi.create_thread.return_value.__enter__ = MagicMock(return_value=thread)
    mqi.create_thread.return_value.__exit__ = MagicMock(return_value=False)
    mqi.__enter__ = MagicMock(return_value=mqi)
    mqi.__exit__ = MagicMock(return_value=False)
    with patch("makeitcompliant.app.prolog.engine.PrologMQI", return_value=mqi):
        engine = PrologEngine(kb_path=str(kb))
        assert engine.query("license_a_permission(X)") == [{"X": "mit"}]
        assert engine.query_atoms("license_a_permission(X)") == ["mit"]
        assert engine.permissions_for_a() == ["mit"]


def test_query_false(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    kb = tmp_path / "facts.pl"
    kb.write_text("% facts\n", encoding="utf-8")
    monkeypatch.setattr(
        "makeitcompliant.app.prolog.engine.get_prolog_runtime_kb_path",
        lambda: kb,
    )
    thread = MagicMock()
    thread.query.return_value = False
    mqi = MagicMock()
    mqi.create_thread.return_value.__enter__ = MagicMock(return_value=thread)
    mqi.create_thread.return_value.__exit__ = MagicMock(return_value=False)
    mqi.__enter__ = MagicMock(return_value=mqi)
    mqi.__exit__ = MagicMock(return_value=False)
    with patch("makeitcompliant.app.prolog.engine.PrologMQI", return_value=mqi):
        assert PrologEngine().query_atoms("goal(X)") is None
