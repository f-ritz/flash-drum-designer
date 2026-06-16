import pytest

from flash_drum_designer import DrumOrientation, FlashDrumInputs, size_flash_drum


def _base_inputs(**overrides) -> FlashDrumInputs:
    defaults = {
        "vapor_mass_flow_kg_s": 3.267,
        "liquid_mass_flow_kg_s": 3.267,
        "vapor_density_kg_m3": 79.42,
        "liquid_density_kg_m3": 843.58,
        "orientation": DrumOrientation.HORIZONTAL,
        "residence_time_min": 5.0,
        "k_factor": 0.107,
        "l_over_d": 4.0,
        "margin": 1.20,
    }
    defaults.update(overrides)
    return FlashDrumInputs(**defaults)


def test_horizontal_reference_case() -> None:
    result = size_flash_drum(_base_inputs())
    assert result.diameter_m == pytest.approx(0.904, rel=1e-3)
    assert result.axial_length_m == pytest.approx(3.617, rel=1e-3)
    assert result.governing_criterion == "liquid residence time"
    assert result.actual_vapor_velocity_m_s < result.max_vapor_velocity_m_s


def test_vertical_uses_smaller_vapor_diameter() -> None:
    horizontal = size_flash_drum(_base_inputs(orientation=DrumOrientation.HORIZONTAL))
    vertical = size_flash_drum(_base_inputs(orientation=DrumOrientation.VERTICAL))
    assert vertical.diameter_from_vapor_m < horizontal.diameter_from_vapor_m


def test_vertical_height_can_be_governed() -> None:
    result = size_flash_drum(
        _base_inputs(
            orientation=DrumOrientation.VERTICAL,
            l_over_d=1.0,
            vertical_vapor_disengagement_ratio=1.0,
        )
    )
    assert result.height_governed is True
    assert result.governing_criterion == "vertical height (liquid + vapor disengagement)"
    assert result.axial_length_m >= result.minimum_vertical_height_m


def test_vapor_disengagement_can_govern_horizontal_drum() -> None:
    result = size_flash_drum(
        _base_inputs(
            vapor_mass_flow_kg_s=20.0,
            liquid_mass_flow_kg_s=0.5,
            residence_time_min=1.0,
        )
    )
    assert result.governing_criterion == "vapor disengagement (Souders-Brown)"


def test_validation_rejects_invalid_densities() -> None:
    with pytest.raises(ValueError, match="Liquid density must be greater than vapor density"):
        _base_inputs(vapor_density_kg_m3=900.0, liquid_density_kg_m3=800.0)


def test_gpsa_k_factor_reduces_with_pressure() -> None:
    low_pressure = size_flash_drum(
        _base_inputs(
            use_gpsa_k_factor=True,
            pressure_bar_gauge=7.0,
            k_factor=None,
        )
    )
    high_pressure = size_flash_drum(
        _base_inputs(
            use_gpsa_k_factor=True,
            pressure_bar_gauge=105.0,
            k_factor=None,
        )
    )
    assert high_pressure.k_factor_used < low_pressure.k_factor_used