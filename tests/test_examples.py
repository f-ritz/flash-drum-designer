import pytest

from flash_drum_designer.examples import EXAMPLES, PROPANE_BUTANE_NGL, get_example
from flash_drum_designer import FlashDrumInputs, size_flash_drum


def test_propane_butane_example_has_realistic_properties() -> None:
    example = PROPANE_BUTANE_NGL
    assert example.liquid_density_kg_m3 > example.vapor_density_kg_m3
    assert example.pressure_bar_gauge > 0
    assert "propane" in example.name.lower()
    assert "butane" in example.name.lower()


def test_example_sizes_successfully() -> None:
    example = EXAMPLES[0]
    inputs = FlashDrumInputs(
        vapor_mass_flow_kg_s=example.vapor_mass_flow_kg_s,
        liquid_mass_flow_kg_s=example.liquid_mass_flow_kg_s,
        vapor_density_kg_m3=example.vapor_density_kg_m3,
        liquid_density_kg_m3=example.liquid_density_kg_m3,
        orientation=example.orientation,
        residence_time_min=example.residence_time_min,
        use_gpsa_k_factor=True,
        pressure_bar_gauge=example.pressure_bar_gauge,
        k_factor=None,
        service_type=example.service_type,
        has_demister=example.has_demister,
        l_over_d=example.l_over_d,
        margin=example.margin,
    )
    result = size_flash_drum(inputs)
    assert result.diameter_m > 0
    assert result.axial_length_m > 0


def test_get_example_unknown_key() -> None:
    with pytest.raises(KeyError):
        get_example("missing")