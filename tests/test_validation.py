from pathlib import Path

import pytest

from makeitcompliant.app.core.validation import (
    UploadedLicense,
    ValidationError,
    read_license_file,
    require_two_licenses,
)


def test_read_license_file_ok(mit_license_file: Path) -> None:
    lic = read_license_file(mit_license_file)
    assert lic.name == "MIT-License"
    assert "MIT" in lic.value


def test_read_missing_file(tmp_path: Path) -> None:
    with pytest.raises(ValidationError, match="not found"):
        read_license_file(tmp_path / "nope.txt")


def test_read_empty_file(tmp_path: Path) -> None:
    p = tmp_path / "empty.txt"
    p.write_text("   \n", encoding="utf-8")
    with pytest.raises(ValidationError, match="empty"):
        read_license_file(p)


def test_read_too_large(tmp_path: Path) -> None:
    p = tmp_path / "big.txt"
    p.write_bytes(b"x" * 6_000_000)
    with pytest.raises(ValidationError, match="too large"):
        read_license_file(p)


def test_read_non_utf8(tmp_path: Path) -> None:
    p = tmp_path / "bin.txt"
    p.write_bytes(b"\xff\xfe")
    with pytest.raises(ValidationError, match="UTF-8"):
        read_license_file(p)


def test_require_two_licenses() -> None:
    a = UploadedLicense("a", "text a")
    b = UploadedLicense("b", "text b")
    assert require_two_licenses([a, b]) == (a, b)
    with pytest.raises(ValidationError):
        require_two_licenses([a])
