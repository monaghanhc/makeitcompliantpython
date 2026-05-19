"""In-memory uploaded license files for the current GUI session."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class LicenseFileEntry:
    name: str
    value: str


@dataclass
class AppSession:
    files: list[LicenseFileEntry] = field(default_factory=list)

    def add(self, name: str, value: str) -> None:
        self.files.append(LicenseFileEntry(name=name, value=value))

    def clear(self) -> None:
        self.files.clear()

    def names_summary(self) -> str:
        return " ".join(f.name for f in self.files)


# Single desktop session (wx runs one main thread)
session = AppSession()
