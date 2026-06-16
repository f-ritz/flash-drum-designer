from pathlib import Path

from flash_drum_designer import (
    DrumOrientation,
    FlashDrumInputs,
    UnitSystem,
    export_result_pdf,
    size_flash_drum,
)
from flash_drum_designer.sizing import DEFAULT_LIQUID_LEVEL_FRACTION, format_result


def _sample_inputs(orientation: DrumOrientation = DrumOrientation.HORIZONTAL) -> FlashDrumInputs:
    return FlashDrumInputs(
        vapor_mass_flow_kg_s=3.267,
        liquid_mass_flow_kg_s=3.267,
        vapor_density_kg_m3=79.42,
        liquid_density_kg_m3=843.58,
        orientation=orientation,
    )


def test_format_result_includes_half_full_liquid_level() -> None:
    inputs = _sample_inputs()
    result = size_flash_drum(inputs)
    text = format_result(inputs, result)
    assert "50% (half-full)" in text


def test_export_pdf_creates_file(tmp_path: Path) -> None:
    inputs = _sample_inputs()
    result = size_flash_drum(inputs)
    pdf_path = tmp_path / "horizontal_report.pdf"

    export_result_pdf(pdf_path, inputs, result, unit_system=UnitSystem.SI)

    assert pdf_path.exists()
    assert pdf_path.stat().st_size > 1000
    assert pdf_path.read_bytes()[:4] == b"%PDF"


def test_export_pdf_vertical_orientation(tmp_path: Path) -> None:
    inputs = _sample_inputs(DrumOrientation.VERTICAL)
    result = size_flash_drum(inputs)
    pdf_path = tmp_path / "vertical_report.pdf"

    export_result_pdf(pdf_path, inputs, result, unit_system=UnitSystem.IMPERIAL)

    assert pdf_path.exists()
    assert result.liquid_level_fraction == DEFAULT_LIQUID_LEVEL_FRACTION