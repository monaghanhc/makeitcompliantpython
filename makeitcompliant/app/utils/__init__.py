from makeitcompliant.app.utils.logging_config import get_logger, setup_logging
from makeitcompliant.app.utils.paths import (
    get_license_templates_dir,
    get_prolog_base_kb_path,
    get_prolog_runtime_kb_path,
    get_resource_root,
    get_web_dir,
)

__all__ = [
    "get_logger",
    "setup_logging",
    "get_resource_root",
    "get_license_templates_dir",
    "get_prolog_base_kb_path",
    "get_prolog_runtime_kb_path",
    "get_web_dir",
]
