"""Scan a project directory for licenses and dependency manifests."""

from __future__ import annotations

import os
from pathlib import Path

from makeitcompliant.app.core.license_registry import atom_to_display
from makeitcompliant.app.ml.license_detector import LicenseDetector
from makeitcompliant.app.scanner import parsers
from makeitcompliant.app.scanner.models import FindingKind, LicenseFinding
from makeitcompliant.app.utils.logging_config import get_logger

logger = get_logger("scanner.project")

SKIP_DIRS = {
    ".git",
    ".hg",
    ".svn",
    "node_modules",
    "vendor",
    "venv",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "dist",
    "build",
    "target",
    ".tox",
    ".eggs",
    "site-packages",
    ".idea",
    ".vscode",
    ".next",
    "coverage",
    "htmlcov",
}

BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".ico", ".pdf", ".zip", ".tar", ".gz",
    ".jar", ".war", ".class", ".dll", ".exe", ".so", ".dylib", ".woff", ".woff2",
    ".pyc", ".pyo", ".whl", ".egg",
}

MAX_FILE_BYTES = 2_000_000
MAX_HEADER_FILES = 120
MAX_DEPTH = 12

LICENSE_FILENAMES = {
    "license",
    "license.txt",
    "license.md",
    "licence",
    "licence.txt",
    "copying",
    "copying.txt",
    "notice",
    "notice.txt",
    "unlicense",
    "unlicense.txt",
}

README_NAMES = {"readme", "readme.md", "readme.txt", "readme.rst"}

MANIFEST_FILES = {
    "package.json",
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "pyproject.toml",
    "setup.py",
    "pipfile",
    "requirements.txt",
    "cargo.toml",
    "go.mod",
    "pom.xml",
    "build.gradle",
    "settings.gradle",
    "gemfile",
    "packages.config",
}

HEADER_EXTENSIONS = {".py", ".js", ".ts", ".tsx", ".java", ".kt", ".go", ".rs", ".c", ".cpp", ".h"}

NOTICE_NAMES = {"notice", "notice.txt", "third_party_notices", "attribution", "authors", "copying"}


class ProjectScanner:
    def __init__(self, detector: LicenseDetector | None = None) -> None:
        self._detector = detector or LicenseDetector()

    def scan(self, project_root: str | Path) -> list[LicenseFinding]:
        root = Path(project_root).resolve()
        if not root.is_dir():
            raise FileNotFoundError(f"Not a directory: {root}")

        findings: list[LicenseFinding] = []
        files_scanned = 0
        header_count = 0
        dep_map: dict[str, str | None] = {}
        project_license: LicenseFinding | None = None

        for dirpath, dirnames, filenames in os.walk(root):
            depth = len(Path(dirpath).relative_to(root).parts)
            if depth > MAX_DEPTH:
                dirnames.clear()
                continue
            dirnames[:] = [
                d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")
            ]

            rel_dir = Path(dirpath).relative_to(root)

            for fname in filenames:
                lower = fname.lower()
                path = Path(dirpath) / fname
                if path.suffix.lower() in BINARY_EXTENSIONS:
                    continue
                try:
                    if path.stat().st_size > MAX_FILE_BYTES:
                        continue
                except OSError:
                    continue
                files_scanned += 1

                if lower in LICENSE_FILENAMES or lower in NOTICE_NAMES:
                    finding = self._classify_file(
                        path, rel_dir / fname, "LICENSE file", FindingKind.PROJECT_LICENSE
                    )
                    findings.append(finding)
                    if project_license is None or finding.confidence > project_license.confidence:
                        project_license = finding
                    continue

                if lower in README_NAMES and rel_dir == Path("."):
                    finding = self._scan_readme(path)
                    findings.append(finding)
                    if finding.license_atom and (
                        project_license is None
                        or finding.confidence > project_license.confidence
                    ):
                        project_license = finding
                    continue

                if lower == "package.json" and rel_dir == Path("."):
                    project_license = self._scan_package_json(path, findings, project_license)
                    continue

                if lower == "package-lock.json":
                    dep_map.update(parsers.parse_package_lock(path))
                    continue

                if lower == "pyproject.toml" and rel_dir == Path("."):
                    atom = parsers.parse_pyproject(path)
                    if atom:
                        project_license = self._finding_from_atom(
                            path, "pyproject.toml", atom, 0.95, FindingKind.PROJECT_LICENSE
                        )
                        findings.append(project_license)
                    continue

                if lower == "setup.py" and rel_dir == Path("."):
                    atom = parsers.parse_setup_py(path)
                    if atom:
                        f = self._finding_from_atom(
                            path, "setup.py", atom, 0.85, FindingKind.PROJECT_LICENSE
                        )
                        findings.append(f)
                        project_license = project_license or f
                    continue

                if lower == "cargo.toml":
                    atom, deps = parsers.parse_cargo_toml(path)
                    if atom and rel_dir == Path("."):
                        project_license = self._finding_from_atom(
                            path, "Cargo.toml", atom, 0.95, FindingKind.PROJECT_LICENSE
                        )
                        findings.append(project_license)
                    for d in deps:
                        dep_map.setdefault(d, None)
                    continue

                if lower == "go.mod" and rel_dir == Path("."):
                    for d in parsers.parse_go_mod(path):
                        dep_map.setdefault(d, None)
                    continue

                if lower == "pom.xml":
                    atom, deps = parsers.parse_pom_xml(path)
                    if atom and rel_dir == Path("."):
                        project_license = self._finding_from_atom(
                            path, "pom.xml", atom, 0.9, FindingKind.PROJECT_LICENSE
                        )
                        findings.append(project_license)
                    for d in deps:
                        dep_map.setdefault(d, None)
                    continue

                if lower == "gemfile":
                    for g in parsers.parse_gemfile(path):
                        dep_map.setdefault(g, None)
                    continue

                if lower.endswith(".csproj"):
                    atom = parsers.parse_csproj(path)
                    if atom and rel_dir == Path("."):
                        project_license = self._finding_from_atom(
                            path, "csproj", atom, 0.8, FindingKind.PROJECT_LICENSE
                        )
                        findings.append(project_license)
                    continue

                if lower == "requirements.txt" and rel_dir == Path("."):
                    for name in parsers.parse_requirements(path):
                        dep_map[name] = None
                    continue

                ext = Path(fname).suffix.lower()
                if ext in HEADER_EXTENSIONS and header_count < MAX_HEADER_FILES:
                    atom = parsers.scan_source_header(path)
                    header_count += 1
                    if atom:
                        findings.append(
                            self._finding_from_atom(
                                path,
                                "source header",
                                atom,
                                0.7,
                                FindingKind.PROJECT_LICENSE,
                            )
                        )

        known_dep_names = {
            f.package_name for f in findings if f.package_name and f.kind == FindingKind.DEPENDENCY
        }
        for name, atom in dep_map.items():
            if name in known_dep_names:
                continue
            if atom:
                findings.append(
                    LicenseFinding(
                        path="manifest",
                        source_kind="dependency manifest",
                        license_atom=atom,
                        display_name=atom_to_display(atom),
                        confidence=0.85,
                        evidence=f"Declared license for {name}",
                        package_name=name,
                        kind=FindingKind.DEPENDENCY,
                    )
                )
            else:
                findings.append(
                    LicenseFinding(
                        path="manifest",
                        source_kind="dependency manifest",
                        license_atom="unknown",
                        display_name="Unknown",
                        confidence=0.0,
                        evidence=f"No license metadata for dependency '{name}'",
                        package_name=name,
                        kind=FindingKind.UNKNOWN,
                    )
                )

        logger.info("Scanned %s files under %s (%d findings)", files_scanned, root, len(findings))
        return findings

    def _classify_file(
        self,
        path: Path,
        rel: Path,
        kind_label: str,
        kind: FindingKind,
    ) -> LicenseFinding:
        text = path.read_text(encoding="utf-8", errors="ignore")[:MAX_FILE_BYTES]
        result = self._detector.detect(text, source=kind_label)
        lic = result.license
        return LicenseFinding(
            path=str(rel),
            source_kind=kind_label,
            license_atom=lic.identifier,
            display_name=lic.display_name,
            confidence=lic.confidence,
            evidence=(
                f"{lic.detection_method}: "
                f"{result.template_filename or lic.matched_text or ''}"
            ),
            kind=kind,
        )

    def _scan_readme(self, path: Path) -> LicenseFinding:
        text = path.read_text(encoding="utf-8", errors="ignore")[:MAX_FILE_BYTES]
        result = self._detector.detect(text, source="README")
        lic = result.license
        return LicenseFinding(
            path="README",
            source_kind="README mention",
            license_atom=lic.identifier,
            display_name=lic.display_name,
            confidence=lic.confidence * 0.95,
            evidence=lic.detection_method,
            kind=FindingKind.PROJECT_LICENSE,
        )

    def _scan_package_json(
        self,
        path: Path,
        findings: list[LicenseFinding],
        project_license: LicenseFinding | None,
    ) -> LicenseFinding | None:
        try:
            atom, deps = parsers.parse_package_json(path)
        except Exception as exc:
            logger.warning("package.json parse error: %s", exc)
            return project_license
        if atom:
            f = self._finding_from_atom(
                path, "package.json", atom, 0.98, FindingKind.PROJECT_LICENSE
            )
            findings.append(f)
            project_license = f
        lock = path.parent / "package-lock.json"
        lock_licenses: dict[str, str | None] = {}
        if lock.is_file():
            try:
                lock_licenses = parsers.parse_package_lock(lock)
            except Exception:
                pass
        for name, _ in deps:
            lic = lock_licenses.get(name)
            if lic:
                findings.append(
                    LicenseFinding(
                        path="package-lock.json",
                        source_kind="npm lockfile",
                        license_atom=lic,
                        display_name=atom_to_display(lic),
                        confidence=0.9,
                        evidence=f"license field in lockfile for {name}",
                        package_name=name,
                        kind=FindingKind.DEPENDENCY,
                    )
                )
            else:
                findings.append(
                    LicenseFinding(
                        path="package.json",
                        source_kind="dependency manifest",
                        license_atom="unknown",
                        display_name="Unknown",
                        confidence=0.0,
                        evidence=f"No license metadata for dependency '{name}'",
                        package_name=name,
                        kind=FindingKind.UNKNOWN,
                    )
                )
        return project_license

    @staticmethod
    def _finding_from_atom(
        path: Path,
        source: str,
        atom: str,
        confidence: float,
        kind: FindingKind,
        rel: Path | None = None,
    ) -> LicenseFinding:
        return LicenseFinding(
            path=str(rel or path.name),
            source_kind=source,
            license_atom=atom,
            display_name=atom_to_display(atom),
            confidence=confidence,
            evidence=f"Parsed from {source}",
            kind=kind,
        )
