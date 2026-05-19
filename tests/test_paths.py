
from makeitcompliant.app.utils.paths import (
    get_license_templates_dir,
    get_prolog_base_kb_path,
    get_resource_root,
)


def test_resource_root_contains_templates() -> None:
    root = get_resource_root()
    assert root.is_dir()
    templates = get_license_templates_dir()
    assert templates.is_dir()
    assert len(list(templates.glob("*.txt"))) >= 40


def test_prolog_base_kb_exists() -> None:
    kb = get_prolog_base_kb_path()
    assert kb.is_file()
    assert kb.name == "allLicenseFactsBaseCopy.pl"
