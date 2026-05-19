from makeitcompliant.app.prolog.analysis_api import (
    DependencyAnalysisResult,
    _parse_list_atoms,
    _parse_list_compounds,
    _parse_result_term,
    parse_dependency_analysis,
    parse_explanation,
    parse_obligations,
    parse_project_report,
)


def test_parse_dependency_compound() -> None:
    row = {"Result": {"functor": "result", "args": ["no", "high", ["strong_copyleft_in_permissive_project"]]}}
    r = parse_dependency_analysis("mit", "gpl_3_0", row)
    assert r.compatible is False
    assert r.risk == "high"


def test_parse_dependency_fallback_keys() -> None:
    row = {"Compatible": "yes", "Risk": "low"}
    r = parse_dependency_analysis("mit", "apache_2_0", row)
    assert r.compatible is True


def test_parse_result_term_none() -> None:
    assert _parse_result_term("bad") is None


def test_parse_list_atoms_prolog_list() -> None:
    cell = {"functor": ".", "args": ["mit", {"functor": ".", "args": ["apache_2_0", []]}]}
    assert _parse_list_atoms(cell) == ["mit", "apache_2_0"]


def test_parse_obligations_variants() -> None:
    rows = [{"Obligations": ["include_copyright_notice"]}, {"X": "state_changes"}, {"Obl": "patent_grant_notice"}]
    obs = parse_obligations(rows)
    assert len(obs) >= 2


def test_parse_obligations_false() -> None:
    assert parse_obligations(False) == []


def test_parse_explanation_variants() -> None:
    assert "compatible" in parse_explanation({"Explanation": "Licenses are compatible"}).lower()
    assert parse_explanation(False) == "No explanation available."
    assert parse_explanation([{"Explanation": "x"}]) == "x"
    assert parse_explanation({"explanation": ["a", "b"]}) == "ab"


def test_parse_project_report_empty() -> None:
    rep = parse_project_report("mit", False, ["apache_2_0"])
    assert rep.overall_risk == "low"
    assert rep.dependency_results == []


def test_parse_project_report_compound() -> None:
    report_term = {
        "functor": "report",
        "args": [
            ["include_copyright_notice"],
            [
                {
                    "functor": "dep_analysis",
                    "args": ["apache_2_0", {"functor": "result", "args": ["yes", "low", []]}],
                }
            ],
            "low",
        ],
    }
    rep = parse_project_report("mit", [{"Report": report_term}], ["apache_2_0"])
    assert rep.obligations
    assert rep.dependency_results[0].compatible is True


def test_parse_project_report_fallback_deps() -> None:
    rep = parse_project_report("mit", [{"Report": "bad"}], ["apache_2_0"])
    assert len(rep.dependency_results) == 1


def test_parse_list_compounds_nested() -> None:
    nested = [{"functor": "dep_analysis", "args": ["x", {"functor": "result", "args": ["yes", "low", []]}]}]
    assert _parse_list_compounds(nested)


def test_dependency_display_property() -> None:
    d = DependencyAnalysisResult("mit", "gpl_3_0", False, "high")
    assert "General Public" in d.dependency_display
