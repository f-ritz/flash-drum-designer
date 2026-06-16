"""Unit conversions between SI and US customary engineering units."""

from __future__ import annotations

from enum import Enum

LB_PER_KG = 2.2046226218
SEC_PER_HOUR = 3600.0
LB_FT3_PER_KG_M3 = 0.0624279606
M_PER_FT = 0.3048
IN_PER_M = 39.3700787402
BAR_PER_PSIG = 0.0689475729


class UnitSystem(str, Enum):
    SI = "si"
    IMPERIAL = "imperial"


def lb_hr_to_kg_s(value: float) -> float:
    return value / LB_PER_KG / SEC_PER_HOUR


def kg_s_to_lb_hr(value: float) -> float:
    return value * LB_PER_KG * SEC_PER_HOUR


def lb_ft3_to_kg_m3(value: float) -> float:
    return value / LB_FT3_PER_KG_M3


def kg_m3_to_lb_ft3(value: float) -> float:
    return value * LB_FT3_PER_KG_M3


def psig_to_bar_gauge(value: float) -> float:
    return value * BAR_PER_PSIG


def bar_gauge_to_psig(value: float) -> float:
    return value / BAR_PER_PSIG


def m_to_ft(value: float) -> float:
    return value / M_PER_FT


def ft_to_m(value: float) -> float:
    return value * M_PER_FT


def m_to_in(value: float) -> float:
    return value * IN_PER_M


def in_to_m(value: float) -> float:
    return value / IN_PER_M