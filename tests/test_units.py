import pytest

from flash_drum_designer.units import (
    bar_gauge_to_psig,
    kg_m3_to_lb_ft3,
    kg_s_to_lb_hr,
    lb_ft3_to_kg_m3,
    lb_hr_to_kg_s,
    m_to_ft,
    psig_to_bar_gauge,
)


def test_mass_flow_round_trip() -> None:
    original_lb_hr = 23574.8
    assert kg_s_to_lb_hr(lb_hr_to_kg_s(original_lb_hr)) == pytest.approx(original_lb_hr, rel=1e-6)


def test_density_round_trip() -> None:
    original_lb_ft3 = 52.65
    assert kg_m3_to_lb_ft3(lb_ft3_to_kg_m3(original_lb_ft3)) == pytest.approx(original_lb_ft3, rel=1e-6)


def test_pressure_round_trip() -> None:
    original_psig = 100.0
    assert bar_gauge_to_psig(psig_to_bar_gauge(original_psig)) == pytest.approx(original_psig, rel=1e-6)


def test_length_conversions() -> None:
    assert m_to_ft(1.0) == pytest.approx(3.28084, rel=1e-4)