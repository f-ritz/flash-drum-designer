import pytest

from flash_drum_designer.k_factor import (
    ServiceType,
    apply_demister_factor,
    apply_service_multiplier,
    lookup_k_factor,
    lookup_k_factor_rule,
    lookup_k_factor_table,
    resolve_k_factor,
)


def test_lookup_k_factor_table_endpoints() -> None:
    assert lookup_k_factor_table(0.0) == pytest.approx(0.107)
    assert lookup_k_factor_table(7.0) == pytest.approx(0.107)
    assert lookup_k_factor_table(105.0) == pytest.approx(0.065)


def test_lookup_k_factor_table_interpolates() -> None:
    assert lookup_k_factor_table(14.0) == pytest.approx(0.104, rel=1e-3)


def test_lookup_k_factor_rule_below_base_pressure() -> None:
    assert lookup_k_factor_rule(3.0) == pytest.approx(0.107)


def test_lookup_k_factor_rule_above_base_pressure() -> None:
    assert lookup_k_factor_rule(21.0) == pytest.approx(0.101)


def test_service_multiplier_override() -> None:
    assert apply_service_multiplier(0.107, ServiceType.STANDARD, multiplier=0.65) == pytest.approx(0.06955)


def test_no_demister_halves_k_factor() -> None:
    assert apply_demister_factor(0.107, has_demister=False) == pytest.approx(0.0535)


def test_resolve_k_factor_manual() -> None:
    k_value, source = resolve_k_factor(
        manual_k_factor=0.095,
        pressure_bar_gauge=None,
        use_gpsa=False,
    )
    assert k_value == pytest.approx(0.095)
    assert source == "manual entry"


def test_resolve_k_factor_gpsa_requires_pressure() -> None:
    with pytest.raises(ValueError, match="Gauge pressure is required"):
        resolve_k_factor(
            manual_k_factor=None,
            pressure_bar_gauge=None,
            use_gpsa=True,
        )


def test_resolve_k_factor_gpsa_with_service_and_no_demister() -> None:
    k_value, source = resolve_k_factor(
        manual_k_factor=None,
        pressure_bar_gauge=7.0,
        use_gpsa=True,
        service_type=ServiceType.GLYCOL_AMINE,
        has_demister=False,
    )
    assert k_value == pytest.approx(0.107 * 0.7 * 0.5)
    assert "GPSA table" in source
    assert "glycol/amine" in source
    assert "no demister" in source