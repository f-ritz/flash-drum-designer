"""GPSA-based Souders-Brown K-factor selection."""

from __future__ import annotations

from enum import Enum

# Gauge pressure (bar) -> K-factor (m/s) for vertical drums with horizontal mesh pads.
GPSA_K_TABLE: tuple[tuple[float, float], ...] = (
    (0.0, 0.107),
    (7.0, 0.107),
    (21.0, 0.101),
    (42.0, 0.092),
    (63.0, 0.083),
    (105.0, 0.065),
)

GPSA_BASE_PRESSURE_BAR = 7.0
GPSA_BASE_K = 0.107
GPSA_PRESSURE_STEP_BAR = 7.0
GPSA_K_DECREMENT_PER_STEP = 0.003


class ServiceType(str, Enum):
    STANDARD = "standard"
    GLYCOL_AMINE = "glycol_amine"
    COMPRESSOR_SUCTION = "compressor_suction"


SERVICE_MULTIPLIER_DEFAULTS: dict[ServiceType, float] = {
    ServiceType.STANDARD: 1.0,
    ServiceType.GLYCOL_AMINE: 0.7,
    ServiceType.COMPRESSOR_SUCTION: 0.75,
}


def lookup_k_factor_table(pressure_bar_gauge: float) -> float:
    """Interpolate K-factor from the GPSA table."""
    if pressure_bar_gauge < 0:
        raise ValueError("Gauge pressure must be zero or positive.")

    if pressure_bar_gauge <= GPSA_K_TABLE[0][0]:
        return GPSA_K_TABLE[0][1]
    if pressure_bar_gauge >= GPSA_K_TABLE[-1][0]:
        return GPSA_K_TABLE[-1][1]

    for (p_low, k_low), (p_high, k_high) in zip(GPSA_K_TABLE, GPSA_K_TABLE[1:]):
        if p_low <= pressure_bar_gauge <= p_high:
            if p_high == p_low:
                return k_low
            fraction = (pressure_bar_gauge - p_low) / (p_high - p_low)
            return k_low + fraction * (k_high - k_low)

    return GPSA_BASE_K


def lookup_k_factor_rule(pressure_bar_gauge: float) -> float:
    """Apply the GPSA rule: K = 0.107 at 7 bar g, minus 0.003 per 7 bar above 7 bar."""
    if pressure_bar_gauge < 0:
        raise ValueError("Gauge pressure must be zero or positive.")
    if pressure_bar_gauge <= GPSA_BASE_PRESSURE_BAR:
        return GPSA_BASE_K

    steps_above_base = (pressure_bar_gauge - GPSA_BASE_PRESSURE_BAR) / GPSA_PRESSURE_STEP_BAR
    return max(GPSA_BASE_K - GPSA_K_DECREMENT_PER_STEP * steps_above_base, 0.0)


def lookup_k_factor(pressure_bar_gauge: float, *, use_rule: bool = False) -> float:
    """Return a GPSA K-factor for the given gauge pressure (bar)."""
    if use_rule:
        return lookup_k_factor_rule(pressure_bar_gauge)
    return lookup_k_factor_table(pressure_bar_gauge)


def apply_service_multiplier(
    k_factor: float,
    service_type: ServiceType,
    *,
    multiplier: float | None = None,
) -> float:
    """Apply GPSA service correction factors."""
    if multiplier is not None:
        if not 0 < multiplier <= 1.5:
            raise ValueError("Service multiplier must be between 0 and 1.5.")
        return k_factor * multiplier
    return k_factor * SERVICE_MULTIPLIER_DEFAULTS[service_type]


def apply_demister_factor(k_factor: float, *, has_demister: bool) -> float:
    """GPSA recommends roughly half the K-value when no mesh pad is installed."""
    return k_factor if has_demister else k_factor * 0.5


def resolve_k_factor(
    *,
    manual_k_factor: float | None,
    pressure_bar_gauge: float | None,
    use_gpsa: bool,
    service_type: ServiceType = ServiceType.STANDARD,
    service_multiplier: float | None = None,
    has_demister: bool = True,
) -> tuple[float, str]:
    """
    Resolve the effective K-factor and describe how it was obtained.

    Manual K takes precedence when GPSA lookup is disabled.
    """
    if use_gpsa:
        if pressure_bar_gauge is None:
            raise ValueError("Gauge pressure is required when GPSA K-factor lookup is enabled.")
        base_k = lookup_k_factor(pressure_bar_gauge)
        source = f"GPSA table at {pressure_bar_gauge:.1f} bar g"
    elif manual_k_factor is not None:
        base_k = manual_k_factor
        source = "manual entry"
    else:
        base_k = GPSA_BASE_K
        source = "default"

    effective_k = apply_service_multiplier(
        base_k,
        service_type,
        multiplier=service_multiplier,
    )
    effective_k = apply_demister_factor(effective_k, has_demister=has_demister)

    if service_type is ServiceType.GLYCOL_AMINE:
        source += ", glycol/amine correction"
    elif service_type is ServiceType.COMPRESSOR_SUCTION:
        source += ", compressor suction correction"
    if not has_demister:
        source += ", no demister correction"

    return effective_k, source