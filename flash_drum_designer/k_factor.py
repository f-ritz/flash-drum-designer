"""GPSA-based Souders-Brown K-factor selection."""

from __future__ import annotations

from dataclasses import dataclass
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


class KFactorMode(str, Enum):
    GPSA = "gpsa"
    MANUAL = "manual"


class PressureRelation(str, Enum):
    """How the selected GPSA pressure relates to the separator operating pressure."""

    AT = "at"
    LESS_THAN = "less_than"
    GREATER_THAN = "greater_than"


@dataclass(frozen=True)
class GpsaPressurePreset:
    """A GPSA table pressure breakpoint."""

    label: str
    pressure_bar_gauge: float
    table_k_factor: float


SERVICE_MULTIPLIER_DEFAULTS: dict[ServiceType, float] = {
    ServiceType.STANDARD: 1.0,
    ServiceType.GLYCOL_AMINE: 0.7,
    ServiceType.COMPRESSOR_SUCTION: 0.75,
}


def gpsa_pressure_presets() -> tuple[GpsaPressurePreset, ...]:
    """Return selectable GPSA pressure breakpoints from the engineering data table."""
    presets = [
        GpsaPressurePreset(
            label=f"{pressure:.0f} bar g  (table K = {k_factor:.3f} m/s)",
            pressure_bar_gauge=pressure,
            table_k_factor=k_factor,
        )
        for pressure, k_factor in GPSA_K_TABLE
    ]
    return tuple(presets)


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


def find_gpsa_bracket(
    pressure_bar_gauge: float,
) -> tuple[float, float, float, float]:
    """Return `(p_low, k_low, p_high, k_high)` for the GPSA interval containing pressure."""
    if pressure_bar_gauge <= GPSA_K_TABLE[0][0]:
        p_low, k_low = GPSA_K_TABLE[0]
        p_high, k_high = GPSA_K_TABLE[1]
        return p_low, k_low, p_high, k_high
    if pressure_bar_gauge >= GPSA_K_TABLE[-1][0]:
        p_low, k_low = GPSA_K_TABLE[-2]
        p_high, k_high = GPSA_K_TABLE[-1]
        return p_low, k_low, p_high, k_high

    for (p_low, k_low), (p_high, k_high) in zip(GPSA_K_TABLE, GPSA_K_TABLE[1:]):
        if p_low <= pressure_bar_gauge <= p_high:
            return p_low, k_low, p_high, k_high

    return GPSA_K_TABLE[0][0], GPSA_K_TABLE[0][1], GPSA_K_TABLE[1][0], GPSA_K_TABLE[1][1]


def resolve_gpsa_lookup_pressure(
    reference_pressure_bar_gauge: float,
    relation: PressureRelation,
) -> tuple[float, str]:
    """
    Return the table pressure used for K lookup and applicability guidance.

    The reference pressure is the selected GPSA breakpoint or custom operating
    pressure entered by the user.
    """
    if reference_pressure_bar_gauge < 0:
        raise ValueError("Gauge pressure must be zero or positive.")

    if relation is PressureRelation.AT:
        lookup_pressure = reference_pressure_bar_gauge
        table_k = lookup_k_factor_table(lookup_pressure)

        if lookup_pressure <= GPSA_BASE_PRESSURE_BAR:
            applicability = (
                f"K = {table_k:.4f} m/s applies to systems with pressure less than or "
                f"equal to {GPSA_BASE_PRESSURE_BAR:.0f} bar g."
            )
        elif lookup_pressure >= GPSA_K_TABLE[-1][0]:
            applicability = (
                f"K = {table_k:.4f} m/s applies to systems with pressure greater than or "
                f"equal to {GPSA_K_TABLE[-1][0]:.0f} bar g."
            )
        else:
            p_low, _, p_high, _ = find_gpsa_bracket(lookup_pressure)
            if abs(lookup_pressure - p_low) < 0.05:
                applicability = (
                    f"Table K = {table_k:.4f} m/s at {lookup_pressure:.0f} bar g. "
                    f"For systems with pressure less than {lookup_pressure:.0f} bar g, use a "
                    f"greater K; for systems with pressure greater than {lookup_pressure:.0f} bar g, "
                    f"use a lower K."
                )
            elif abs(lookup_pressure - p_high) < 0.05:
                applicability = (
                    f"Table K = {table_k:.4f} m/s at {lookup_pressure:.0f} bar g. "
                    f"For systems with pressure less than {lookup_pressure:.0f} bar g, use a "
                    f"greater K; for systems with pressure greater than {lookup_pressure:.0f} bar g, "
                    f"use a lower K."
                )
            else:
                applicability = (
                    f"K = {table_k:.4f} m/s interpolated at {lookup_pressure:.1f} bar g "
                    f"(between {p_low:.0f} and {p_high:.0f} bar g)."
                )
        return lookup_pressure, applicability

    if relation is PressureRelation.LESS_THAN:
        if reference_pressure_bar_gauge <= GPSA_BASE_PRESSURE_BAR:
            lookup_pressure = GPSA_K_TABLE[0][0]
            table_k = lookup_k_factor_table(lookup_pressure)
            applicability = (
                f"K = {table_k:.4f} m/s applies to systems with pressure less than or "
                f"equal to {reference_pressure_bar_gauge:.1f} bar g."
            )
            return lookup_pressure, applicability

        p_low, _, _, _ = find_gpsa_bracket(reference_pressure_bar_gauge)
        lookup_pressure = p_low
        table_k = lookup_k_factor_table(lookup_pressure)
        applicability = (
            f"K = {table_k:.4f} m/s applies to systems with pressure less than "
            f"{reference_pressure_bar_gauge:.1f} bar g "
            f"(GPSA endpoint at {lookup_pressure:.0f} bar g)."
        )
        return lookup_pressure, applicability

    if reference_pressure_bar_gauge >= GPSA_K_TABLE[-1][0]:
        lookup_pressure = GPSA_K_TABLE[-1][0]
        table_k = lookup_k_factor_table(lookup_pressure)
        applicability = (
            f"K = {table_k:.4f} m/s applies to systems with pressure greater than or "
            f"equal to {reference_pressure_bar_gauge:.1f} bar g."
        )
        return lookup_pressure, applicability

    lookup_pressure: float | None = None
    for index, (table_pressure, _) in enumerate(GPSA_K_TABLE):
        if abs(reference_pressure_bar_gauge - table_pressure) < 0.05:
            lookup_pressure = GPSA_K_TABLE[min(index + 1, len(GPSA_K_TABLE) - 1)][0]
            break

    if lookup_pressure is None:
        _, _, p_high, _ = find_gpsa_bracket(reference_pressure_bar_gauge)
        lookup_pressure = p_high

    table_k = lookup_k_factor_table(lookup_pressure)
    applicability = (
        f"K = {table_k:.4f} m/s applies to systems with pressure greater than "
        f"{reference_pressure_bar_gauge:.1f} bar g "
        f"(GPSA endpoint at {lookup_pressure:.0f} bar g)."
    )
    return lookup_pressure, applicability


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
    pressure_relation: PressureRelation = PressureRelation.AT,
    service_type: ServiceType = ServiceType.STANDARD,
    service_multiplier: float | None = None,
    has_demister: bool = True,
) -> tuple[float, str, str]:
    """
    Resolve the effective K-factor and describe how it was obtained.

    Manual K takes precedence when GPSA lookup is disabled.
    """
    applicability = ""

    if use_gpsa:
        if pressure_bar_gauge is None:
            raise ValueError("Gauge pressure is required when GPSA K-factor lookup is enabled.")
        lookup_pressure, applicability = resolve_gpsa_lookup_pressure(
            pressure_bar_gauge,
            pressure_relation,
        )
        base_k = lookup_k_factor(lookup_pressure)
        source = (
            f"GPSA table (reference {pressure_bar_gauge:.1f} bar g, "
            f"lookup {lookup_pressure:.1f} bar g, base K = {base_k:.4f} m/s)"
        )
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

    return effective_k, source, applicability


def preview_k_factor(
    *,
    mode: KFactorMode,
    pressure_bar_gauge: float | None,
    manual_k_factor: float | None,
    service_type: ServiceType,
    has_demister: bool,
    pressure_relation: PressureRelation = PressureRelation.AT,
) -> tuple[float, str, float | None, str]:
    """
    Return effective K, source text, and GPSA base K for UI preview.

    The third value is the interpolated GPSA table K before service/demister
    corrections. It is None in manual mode.
    """
    use_gpsa = mode is KFactorMode.GPSA
    effective_k, source, applicability = resolve_k_factor(
        manual_k_factor=manual_k_factor,
        pressure_bar_gauge=pressure_bar_gauge,
        use_gpsa=use_gpsa,
        pressure_relation=pressure_relation,
        service_type=service_type,
        has_demister=has_demister,
    )
    if use_gpsa and pressure_bar_gauge is not None:
        lookup_pressure, _ = resolve_gpsa_lookup_pressure(pressure_bar_gauge, pressure_relation)
        base_k = lookup_k_factor(lookup_pressure)
    else:
        base_k = None
    return effective_k, source, base_k, applicability