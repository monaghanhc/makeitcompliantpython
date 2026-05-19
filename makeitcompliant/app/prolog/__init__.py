from makeitcompliant.app.prolog.analysis_api import (
    DependencyAnalysisResult,
    ProjectAnalysisReport,
)
from makeitcompliant.app.prolog.engine import PrologEngine, PrologEngineError
from makeitcompliant.app.prolog.facts_loader import write_runtime_facts
from makeitcompliant.app.prolog.reasoning_engine import ComplianceReasoningEngine

__all__ = [
    "ComplianceReasoningEngine",
    "DependencyAnalysisResult",
    "ProjectAnalysisReport",
    "PrologEngine",
    "PrologEngineError",
    "write_runtime_facts",
]
