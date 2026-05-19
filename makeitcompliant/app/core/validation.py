"""Input validation for uploaded license files."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class UploadedLicense:
    name: str
    value: str
    path: Path | None = None


class ValidationError(ValueError):
    pass


def read_license_file(path: str | Path, *, max_bytes: int = 5_000_000) -> UploadedLicense:
    file_path = Path(path)
    if not file_path.is_file():
        raise ValidationError(f"File not found: {file_path}")
    size = file_path.stat().st_size
    if size > max_bytes:
        raise ValidationError(f"File too large (max {max_bytes} bytes): {file_path}")
    try:
        content = file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ValidationError(f"File must be UTF-8 text: {file_path}") from exc
    if not content.strip():
        raise ValidationError(f"File is empty: {file_path}")
    name = file_path.stem
    return UploadedLicense(name=name, value=content, path=file_path)


def require_two_licenses(files: list[UploadedLicense]) -> tuple[UploadedLicense, UploadedLicense]:
    if len(files) < 2:
        raise ValidationError("Upload at least two license files to compare or analyze.")
    return files[0], files[1]
