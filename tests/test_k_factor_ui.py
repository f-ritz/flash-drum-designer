import pytest

from flash_drum_designer.k_factor import (
    KFactorMode,
    PressureRelation,
    ServiceType,
    gpsa_pressure_presets,
    lookup_k_factor_table,
    preview_k_factor,
)


def test_gpsa_pressure_presets_match_table() -> None:
    presets = gpsa_pressure_presets()
    assert len(presets) == 6
    assert presets[1].pressure_bar_gauge == 7.0
    assert presets[1].table_k_factor == pytest.approx(0.107)


def test_preview_k_factor_gpsa_at_17_bar() -> None:
    effective_k, source, base_k, applicability = preview_k_factor(
        mode=KFactorMode.GPSA,
        pressure_bar_gauge=17.2,
        manual_k_factor=None,
        service_type=ServiceType.STANDARD,
        has_demister=True,
        pressure_relation=PressureRelation.AT,
    )
    assert base_k == pytest.approx(lookup_k_factor_table(17.2), rel=1e-6)
    assert effective_k == pytest.approx(base_k)
    assert "GPSA table" in source
    assert "between 7 and 21 bar g" in applicability


def test_preview_k_factor_manual_mode() -> None:
    effective_k, source, base_k, applicability = preview_k_factor(
        mode=KFactorMode.MANUAL,
        pressure_bar_gauge=None,
        manual_k_factor=0.095,
        service_type=ServiceType.STANDARD,
        has_demister=True,
    )
    assert effective_k == pytest.approx(0.095)
    assert base_k is None
    assert applicability == ""
    assert source == "manual entry"


def test_preview_k_factor_below_selected_pressure() -> None:
    effective_k, _, base_k, applicability = preview_k_factor(
        mode=KFactorMode.GPSA,
        pressure_bar_gauge=21.0,
        manual_k_factor=None,
        service_type=ServiceType.STANDARD,
        has_demister=True,
        pressure_relation=PressureRelation.LESS_THAN,
    )
    assert base_k == pytest.approx(0.107)
    assert effective_k == pytest.approx(0.107)
    assert "less than 21.0 bar g" in applicability