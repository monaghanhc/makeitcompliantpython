"""SWI-Prolog MQI bridge for license queries."""

from __future__ import annotations

from typing import Any

from swiplserver import PrologMQI

from makeitcompliant.app.utils.logging_config import get_logger
from makeitcompliant.app.utils.paths import get_prolog_runtime_kb_path, prolog_path_for_consult

logger = get_logger("prolog.engine")


class PrologEngineError(RuntimeError):
    pass


class PrologEngine:
    """Query the generated allLicenseFacts.pl via SWI-Prolog MQI."""

    def __init__(self, kb_path: str | None = None) -> None:
        self._kb_path = kb_path or prolog_path_for_consult(get_prolog_runtime_kb_path())

    def query(self, goal: str) -> list[dict[str, Any]] | False:
        if not get_prolog_runtime_kb_path().is_file():
            raise PrologEngineError(
                "Runtime Prolog KB missing. Classify a license first to generate "
                "allLicenseFacts.pl."
            )
        try:
            with PrologMQI() as mqi:
                with mqi.create_thread() as thread:
                    consult = f'consult("{self._kb_path}").'
                    thread.query(consult)
                    return thread.query(goal)
        except Exception as exc:
            logger.exception("Prolog query failed: %s", goal)
            raise PrologEngineError(f"Prolog query failed: {exc}") from exc

    def query_atoms(self, goal: str, variable: str = "X") -> list[str] | None:
        result = self.query(goal)
        if result is False:
            return None
        return [row[variable] for row in result if variable in row]

    def permissions_for_a(self) -> list[str] | None:
        return self.query_atoms("license_a_permission(X).")

    def permissions_for_b(self) -> list[str] | None:
        return self.query_atoms("license_b_permission(X).")

    def conditions_distribution_a(self) -> list[str] | None:
        return self.query_atoms("license_a_conditions_before_distribution(X).")

    def conditions_distribution_b(self) -> list[str] | None:
        return self.query_atoms("license_b_conditions_before_distribution(X).")

    def conditions_modification_a(self) -> list[str] | None:
        return self.query_atoms("license_a_conditions_before_modification(X).")

    def conditions_modification_b(self) -> list[str] | None:
        return self.query_atoms("license_b_conditions_before_modification(X).")

    def limitations_a(self) -> list[str] | None:
        return self.query_atoms("license_a_limitation(X).")

    def limitations_b(self) -> list[str] | None:
        return self.query_atoms("license_b_limitation(X).")
