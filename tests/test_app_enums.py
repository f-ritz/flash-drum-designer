"""Regression tests for PySide6 combo enum round-tripping."""

import pytest

from flash_drum_designer import DrumOrientation, ServiceType, UnitSystem, format_result, size_flash_drum
from flash_drum_designer.examples import EXAMPLES
from flash_drum_designer.k_factor import KFactorMode, PressureRelation
from flash_drum_designer.sizing import FlashDrumInputs


def test_format_result_accepts_enum_orientation_not_string() -> None:
    """format_result must receive Enum members, not raw combo strings."""
    ex = EXAMPLES[0]
    inputs = FlashDrumInputs(
        vapor_mass_flow_kg_s=ex.vapor_mass_flow_kg_s,
        liquid_mass_flow_kg_s=ex.liquid_mass_flow_kg_s,
        vapor_density_kg_m3=ex.vapor_density_kg_m3,
        liquid_density_kg_m3=ex.liquid_density_kg_m3,
        orientation=DrumOrientation.HORIZONTAL,
        use_gpsa_k_factor=True,
        pressure_bar_gauge=ex.pressure_bar_gauge,
        k_factor=None,
        pressure_relation=PressureRelation.AT,
        service_type=ServiceType.STANDARD,
    )
    result = size_flash_drum(inputs)
    text = format_result(inputs, result, unit_system=UnitSystem.SI)
    assert "Diameter" in text
    assert "1.183" in text


def test_string_orientation_breaks_format_result() -> None:
    ex = EXAMPLES[0]
    inputs = FlashDrumInputs(
        vapor_mass_flow_kg_s=ex.vapor_mass_flow_kg_s,
        liquid_mass_flow_kg_s=ex.liquid_mass_flow_kg_s,
        vapor_density_kg_m3=ex.vapor_density_kg_m3,
        liquid_density_kg_m3=ex.liquid_density_kg_m3,
        orientation="horizontal",  # type: ignore[arg-type]
        use_gpsa_k_factor=True,
        pressure_bar_gauge=ex.pressure_bar_gauge,
        k_factor=None,
    )
    result = size_flash_drum(inputs)
    with pytest.raises(AttributeError):
        format_result(inputs, result, unit_system=UnitSystem.SI)