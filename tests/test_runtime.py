from unittest.mock import MagicMock, patch

from makeitcompliant.app.prolog.runtime import check_prolog, require_prolog


def test_check_prolog_not_found() -> None:
    with patch("makeitcompliant.app.prolog.runtime.shutil.which", return_value=None):
        status = check_prolog()
    assert not status.available
    assert "not found" in status.message.lower()


def test_check_prolog_ok() -> None:
    with patch("makeitcompliant.app.prolog.runtime.shutil.which", return_value="/usr/bin/swipl"):
        proc = MagicMock()
        proc.stdout = "SWI-Prolog version 9.0\n"
        proc.stderr = ""
        with patch("makeitcompliant.app.prolog.runtime.subprocess.run", return_value=proc):
            status = check_prolog()
    assert status.available
    assert status.version_line


def test_check_prolog_run_error() -> None:
    with patch("makeitcompliant.app.prolog.runtime.shutil.which", return_value="/swipl"):
        with patch(
            "makeitcompliant.app.prolog.runtime.subprocess.run",
            side_effect=OSError("boom"),
        ):
            status = check_prolog()
    assert not status.available


def test_require_prolog() -> None:
    with patch("makeitcompliant.app.prolog.runtime.check_prolog") as mock:
        mock.return_value = MagicMock(available=False, message="x")
        assert require_prolog().available is False
