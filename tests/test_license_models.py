from makeitcompliant.app.core.license_models import (
    define,
    describe_fact,
    normalize_template_name_to_prolog,
)


def test_describe_fact_known() -> None:
    assert describe_fact("can_use_commercially") is not None


def test_describe_fact_unknown() -> None:
    assert describe_fact("not_a_real_fact_xyz") is None
    assert define("not_a_real_fact_xyz") is False


def test_normalize_unknown_template() -> None:
    assert normalize_template_name_to_prolog("Custom License XYZ.txt") == "Custom License XYZ"
