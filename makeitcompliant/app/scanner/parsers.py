"""Extract license identifiers from manifest and metadata files."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any
from xml.etree import ElementTree

from makeitcompliant.app.core.license_registry import (
    extract_spdx_from_text,
    manifest_value_to_atom,
)

_PYPROJECT_LICENSE = re.compile(
    r'^\s*license\s*=\s*["\']([^"\']+)["\']',
    re.MULTILINE | re.IGNORECASE,
)
_CARGO_LICENSE = re.compile(
    r'^\s*license\s*=\s*["\']([^"\']+)["\']',
    re.MULTILINE | re.IGNORECASE,
)
_GEM_LICENSE = re.compile(
    r"^\s*license\s+['\"]([^'\"]+)['\"]",
    re.MULTILINE | re.IGNORECASE,
)
_HEADER_SPDX = re.compile(
    r"SPDX-License-Identifier:\s*([A-Za-z0-9.-]+)",
    re.IGNORECASE,
)
_HEADER_COPYLEFT = re.compile(
    r"(?:GNU\s+)?(GPL|LGPL|AGPL)[\s-]*(v?ersion)?\s*([23](?:\.\d+)?)",
    re.IGNORECASE,
)


def parse_package_json(path: Path) -> tuple[str | None, list[tuple[str, str | None]]]:
    """Return (project_license_atom, [(dep_name, license_atom|None)])."""
    data = json.loads(path.read_text(encoding="utf-8"))
    project_atom = _license_field_to_atom(data.get("license"))
    deps: list[tuple[str, str | None]] = []
    for section in ("dependencies", "devDependencies", "peerDependencies"):
        block = data.get(section) or {}
        if isinstance(block, dict):
            for name in block:
                deps.append((name, None))
    return project_atom, deps


def parse_package_lock(path: Path) -> dict[str, str | None]:
    """Map package name -> license atom from package-lock.json."""
    data = json.loads(path.read_text(encoding="utf-8"))
    result: dict[str, str | None] = {}
    packages = data.get("packages") or {}
    for key, meta in packages.items():
        if not isinstance(meta, dict):
            continue
        name = key.split("node_modules/")[-1] if key else ""
        if not name or name == "":
            continue
        lic = meta.get("license")
        if isinstance(lic, dict):
            lic = lic.get("type")
        atom = _license_field_to_atom(lic) if lic else None
        if atom:
            result[name] = atom
    return result


def parse_pyproject(path: Path) -> str | None:
    text = path.read_text(encoding="utf-8")
    try:
        import tomllib

        data = tomllib.loads(text)
        project = data.get("project") or {}
        lic = project.get("license")
        if isinstance(lic, dict):
            return manifest_value_to_atom(str(lic.get("text", "")))
        if isinstance(lic, str):
            return manifest_value_to_atom(lic)
    except Exception:
        pass
    match = _PYPROJECT_LICENSE.search(text)
    return manifest_value_to_atom(match.group(1)) if match else extract_spdx_from_text(text)


def parse_setup_py(path: Path) -> str | None:
    text = path.read_text(encoding="utf-8", errors="ignore")
    match = re.search(r"license\s*=\s*['\"]([^'\"]+)['\"]", text, re.I)
    return manifest_value_to_atom(match.group(1)) if match else extract_spdx_from_text(text)


def parse_requirements(path: Path) -> list[str]:
    """Dependency names only (no license in requirements.txt)."""
    names: list[str] = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        name = re.split(r"[<>=!~\[]", line)[0].strip()
        if name:
            names.append(name)
    return names


def parse_cargo_toml(path: Path) -> tuple[str | None, list[str]]:
    text = path.read_text(encoding="utf-8")
    lic_match = _CARGO_LICENSE.search(text)
    project = manifest_value_to_atom(lic_match.group(1)) if lic_match else None
    deps: list[str] = []
    in_deps = False
    for line in text.splitlines():
        if re.match(r"^\[.*dependencies", line):
            in_deps = True
            continue
        if line.startswith("[") and in_deps:
            in_deps = False
        if in_deps:
            m = re.match(r"^([a-zA-Z0-9_-]+)\s*=", line)
            if m:
                deps.append(m.group(1))
    return project, deps


def parse_go_mod(path: Path) -> list[str]:
    deps: list[str] = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if line.startswith("require "):
            parts = line.replace("require ", "").split()
            if parts:
                deps.append(parts[0].strip("()"))
        elif line.startswith("\t") and " " in line:
            module = line.strip().split()[0]
            if "/" in module:
                deps.append(module)
    return deps


def parse_pom_xml(path: Path) -> tuple[str | None, list[str]]:
    tree = ElementTree.parse(path)
    root = tree.getroot()
    ns = {"m": "http://maven.apache.org/POM/4.0.0"}

    def _tag(name: str) -> str:
        return f"{{http://maven.apache.org/POM/4.0.0}}{name}"

    licenses: list[str] = []
    for lic in root.findall(".//m:licenses/m:license/m:name", ns) or root.findall(
        ".//license/name"
    ):
        if lic.text:
            atom = manifest_value_to_atom(lic.text)
            if atom:
                licenses.append(atom)
    project = licenses[0] if licenses else None
    deps: list[str] = []
    for dep in root.findall(".//m:dependency", ns) or root.findall(".//dependency"):
        artifact = dep.find(_tag("artifactId"))
        if artifact is not None and artifact.text:
            deps.append(artifact.text)
    return project, deps


def parse_gemfile(path: Path) -> list[str]:
    gems: list[str] = []
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        m = re.match(r'gem\s+["\']([^"\']+)["\']', line.strip())
        if m:
            gems.append(m.group(1))
    return gems


def parse_csproj(path: Path) -> str | None:
    text = path.read_text(encoding="utf-8", errors="ignore")
    return extract_spdx_from_text(text)


def scan_source_header(path: Path, max_lines: int = 40) -> str | None:
    try:
        lines = []
        with path.open(encoding="utf-8", errors="ignore") as fh:
            for i, line in enumerate(fh):
                if i >= max_lines:
                    break
                lines.append(line)
        text = "".join(lines)
    except OSError:
        return None
    spdx = extract_spdx_from_text(text)
    if spdx:
        return spdx
    m = _HEADER_COPYLEFT.search(text)
    if m:
        family, _, ver = m.group(1).upper(), m.group(2), m.group(3) or ""
        if "AGPL" in family:
            return "agpl_3_0"
        if "LGPL" in family:
            return "lgpl_3_0" if ver.startswith("3") else "lgpl_2_1"
        if "GPL" in family:
            return "gpl_3_0" if ver.startswith("3") else "gpl_2_0"
    if "mit license" in text.lower():
        return "mit"
    if "apache license" in text.lower() and "2.0" in text.lower():
        return "apache_2_0"
    return None


def _license_field_to_atom(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, list):
        for item in value:
            atom = _license_field_to_atom(item)
            if atom:
                return atom
        return None
    if isinstance(value, dict):
        return manifest_value_to_atom(str(value.get("type", value.get("name", ""))))
    return manifest_value_to_atom(str(value))
