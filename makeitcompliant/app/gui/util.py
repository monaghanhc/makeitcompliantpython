"""GUI helpers without coupling panels to a specific frame type."""

from __future__ import annotations

from typing import Any, Protocol


class LicenseAnalysisHost(Protocol):
    def get_license_pair_analysis(self) -> Any: ...


def find_main_frame(window: Any) -> LicenseAnalysisHost | None:
    """Walk parents until we find the frame that exposes license pair analysis."""
    current = window
    while current is not None:
        if "get_license_pair_analysis" in type(current).__dict__:
            return current  # type: ignore[return-value]
        get_parent = getattr(current, "GetParent", None)
        current = get_parent() if callable(get_parent) else None
    return None
