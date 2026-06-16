"""Flash drum sizing using Souders-Brown and liquid residence time."""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum

from flash_drum_designer.k_factor import PressureRelation, ServiceType, resolve_k_factor
from flash_drum_designer.units import UnitSystem, bar_gauge_to_psig, kg_m3_to_lb_ft3, kg_s_to_lb_hr, m_to_ft, m_to_in

DEFAULT_LIQUID_LEVEL_FRACTION = 0.5


class DrumOrientation(str, Enum):
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"


@dataclass(frozen=True)
class FlashDrumInputs:
    """
    Process conditions for an isenthalpic FLASH2-style separator.

    No heat duty is modeled: outlet stream flows and densities are taken directly
    from simulator results and treated as the drum design basis.
    """

    vapor_mass_flow_kg_s: float
    liquid_mass_flow_kg_s: float
    vapor_density_kg_m3: float
    liquid_density_kg_m3: float
    orientation: DrumOrientation = DrumOrientation.HORIZONTAL
    residence_time_min: float = 5.0
    k_factor: float | None = 0.107
    use_gpsa_k_factor: bool = False
    pressure_bar_gauge: float | None = None
    pressure_relation: PressureRelation = PressureRelation.AT
    service_type: ServiceType = ServiceType.STANDARD
    service_multiplier: float | None = None
    has_demister: bool = True
    l_over_d: float = 4.0
    margin: float = 1.20
    vertical_vapor_disengagement_ratio: float = 0.75

    def __post_init__(self) -> None:
        if self.vapor_mass_flow_kg_s <= 0:
            raise ValueError("Vapor mass flow must be greater than zero.")
        if self.liquid_mass_flow_kg_s <= 0:
            raise ValueError("Liquid mass flow must be greater than zero.")
        if self.vapor_density_kg_m3 <= 0:
            raise ValueError("Vapor density must be greater than zero.")
        if self.liquid_density_kg_m3 <= 0:
            raise ValueError("Liquid density must be greater than zero.")
        if self.liquid_density_kg_m3 <= self.vapor_density_kg_m3:
            raise ValueError("Liquid density must be greater than vapor density.")
        if self.residence_time_min <= 0:
            raise ValueError("Residence time must be greater than zero.")
        if self.k_factor is not None and self.k_factor <= 0:
            raise ValueError("K-factor must be greater than zero.")
        if self.l_over_d <= 0:
            raise ValueError("L/D (or H/D) ratio must be greater than zero.")
        if self.margin < 1.0:
            raise ValueError("Safety margin must be at least 1.0.")
        if self.vertical_vapor_disengagement_ratio <= 0:
            raise ValueError("Vertical vapor disengagement ratio must be greater than zero.")
        if self.pressure_bar_gauge is not None and self.pressure_bar_gauge < 0:
            raise ValueError("Gauge pressure must be zero or positive.")

    def _resolved_k_factor(self) -> tuple[float, str, str]:
        return resolve_k_factor(
            manual_k_factor=self.k_factor,
            pressure_bar_gauge=self.pressure_bar_gauge,
            use_gpsa=self.use_gpsa_k_factor,
            pressure_relation=self.pressure_relation,
            service_type=self.service_type,
            service_multiplier=self.service_multiplier,
            has_demister=self.has_demister,
        )

    @property
    def effective_k_factor(self) -> float:
        k_value, _, _ = self._resolved_k_factor()
        return k_value

    @property
    def k_factor_source(self) -> str:
        _, source, _ = self._resolved_k_factor()
        return source

    @property
    def k_factor_applicability(self) -> str:
        _, _, applicability = self._resolved_k_factor()
        return applicability


@dataclass(frozen=True)
class FlashDrumResult:
    """Sized drum geometry and vapor-side checks."""

    orientation: DrumOrientation
    diameter_m: float
    axial_length_m: float
    max_vapor_velocity_m_s: float
    actual_vapor_velocity_m_s: float
    vapor_volumetric_flow_m3_s: float
    liquid_volumetric_flow_m3_s: float
    diameter_from_vapor_m: float
    diameter_from_liquid_m: float
    governing_criterion: str
    k_factor_used: float
    k_factor_source: str
    liquid_height_m: float
    liquid_level_fraction: float = DEFAULT_LIQUID_LEVEL_FRACTION
    minimum_vertical_height_m: float | None = None
    height_governed: bool = False

    @property
    def diameter_in(self) -> float:
        return m_to_in(self.diameter_m)

    @property
    def axial_length_in(self) -> float:
        return m_to_in(self.axial_length_m)

    @property
    def diameter_ft(self) -> float:
        return m_to_ft(self.diameter_m)

    @property
    def axial_length_ft(self) -> float:
        return m_to_ft(self.axial_length_m)

    @property
    def axial_over_d(self) -> float:
        return self.axial_length_m / self.diameter_m


def _vapor_area_fraction(inputs: FlashDrumInputs) -> float:
    """Horizontal drums use half the cross-section for vapor at 50% liquid level."""
    if inputs.orientation is DrumOrientation.VERTICAL:
        return 1.0
    return 1 - DEFAULT_LIQUID_LEVEL_FRACTION


def _diameter_from_vapor(vapor_flow_m3_s: float, max_vapor_velocity: float, inputs: FlashDrumInputs) -> float:
    vapor_area_required = vapor_flow_m3_s / max_vapor_velocity * inputs.margin
    vapor_area_fraction = _vapor_area_fraction(inputs)
    return math.sqrt(4 * vapor_area_required / (math.pi * vapor_area_fraction))


def _diameter_from_liquid(liquid_flow_m3_s: float, inputs: FlashDrumInputs) -> float:
    liquid_holdup_volume = liquid_flow_m3_s * inputs.residence_time_min * 60
    total_volume_required = liquid_holdup_volume / DEFAULT_LIQUID_LEVEL_FRACTION
    return (4 * total_volume_required / (math.pi * inputs.l_over_d)) ** (1 / 3)


def size_flash_drum(inputs: FlashDrumInputs) -> FlashDrumResult:
    """
    Size a two-phase isenthalpic flash drum from outlet stream data.

    The governing diameter is the larger of:
    1. Souders-Brown vapor disengagement
    2. Liquid holdup for the requested residence time

    Vertical drums use the full cross-section for vapor and may increase height
    when liquid inventory plus minimum vapor disengagement exceeds H/D sizing.
    """
    vapor_flow_m3_s = inputs.vapor_mass_flow_kg_s / inputs.vapor_density_kg_m3
    liquid_flow_m3_s = inputs.liquid_mass_flow_kg_s / inputs.liquid_density_kg_m3

    density_ratio = (inputs.liquid_density_kg_m3 - inputs.vapor_density_kg_m3) / inputs.vapor_density_kg_m3
    k_factor_used = inputs.effective_k_factor
    k_factor_source = inputs.k_factor_source
    max_vapor_velocity = k_factor_used * math.sqrt(density_ratio)

    diameter_from_vapor = _diameter_from_vapor(vapor_flow_m3_s, max_vapor_velocity, inputs)
    diameter_from_liquid = _diameter_from_liquid(liquid_flow_m3_s, inputs)

    diameter_m = max(diameter_from_vapor, diameter_from_liquid)
    axial_length_m = inputs.l_over_d * diameter_m
    liquid_holdup_volume = liquid_flow_m3_s * inputs.residence_time_min * 60
    liquid_height_m = liquid_holdup_volume / (math.pi * diameter_m**2 / 4)

    minimum_vertical_height_m: float | None = None
    height_governed = False

    if inputs.orientation is DrumOrientation.VERTICAL:
        minimum_vertical_height_m = liquid_height_m + inputs.vertical_vapor_disengagement_ratio * diameter_m
        if minimum_vertical_height_m > axial_length_m:
            axial_length_m = minimum_vertical_height_m
            height_governed = True

    vapor_area_fraction = _vapor_area_fraction(inputs)
    vapor_area_actual = (math.pi * diameter_m**2 / 4) * vapor_area_fraction
    actual_vapor_velocity = vapor_flow_m3_s / vapor_area_actual

    if height_governed:
        governing_criterion = "vertical height (liquid + vapor disengagement)"
    elif diameter_from_vapor >= diameter_from_liquid:
        governing_criterion = "vapor disengagement (Souders-Brown)"
    else:
        governing_criterion = "liquid residence time"

    return FlashDrumResult(
        orientation=inputs.orientation,
        diameter_m=diameter_m,
        axial_length_m=axial_length_m,
        max_vapor_velocity_m_s=max_vapor_velocity,
        actual_vapor_velocity_m_s=actual_vapor_velocity,
        vapor_volumetric_flow_m3_s=vapor_flow_m3_s,
        liquid_volumetric_flow_m3_s=liquid_flow_m3_s,
        diameter_from_vapor_m=diameter_from_vapor,
        diameter_from_liquid_m=diameter_from_liquid,
        governing_criterion=governing_criterion,
        k_factor_used=k_factor_used,
        k_factor_source=k_factor_source,
        liquid_height_m=liquid_height_m,
        liquid_level_fraction=DEFAULT_LIQUID_LEVEL_FRACTION,
        minimum_vertical_height_m=minimum_vertical_height_m,
        height_governed=height_governed,
    )


def size_horizontal_flash_drum(inputs: FlashDrumInputs) -> FlashDrumResult:
    """Backward-compatible wrapper for horizontal sizing."""
    if inputs.orientation is not DrumOrientation.HORIZONTAL:
        raise ValueError("Inputs orientation must be horizontal.")
    return size_flash_drum(inputs)


def format_result(
    inputs: FlashDrumInputs,
    result: FlashDrumResult,
    *,
    unit_system: UnitSystem = UnitSystem.SI,
) -> str:
    """Return a human-readable sizing summary."""
    orientation_label = inputs.orientation.value.capitalize()
    axial_label = "Length" if inputs.orientation is DrumOrientation.HORIZONTAL else "Height"

    if unit_system is UnitSystem.IMPERIAL:
        diameter_line = (
            f"  Diameter            : {result.diameter_ft:.3f} ft ({result.diameter_in:.1f} in)"
        )
        axial_line = (
            f"  {axial_label:<19}: {result.axial_length_ft:.3f} ft ({result.axial_length_in:.1f} in)"
        )
        vapor_mass = kg_s_to_lb_hr(inputs.vapor_mass_flow_kg_s)
        liquid_mass = kg_s_to_lb_hr(inputs.liquid_mass_flow_kg_s)
        vapor_density = kg_m3_to_lb_ft3(inputs.vapor_density_kg_m3)
        liquid_density = kg_m3_to_lb_ft3(inputs.liquid_density_kg_m3)
        mass_unit = "lb/hr"
        density_unit = "lb/ft³"
        pressure_line = (
            f"  Operating pressure  : {bar_gauge_to_psig(inputs.pressure_bar_gauge):.1f} psig"
            if inputs.pressure_bar_gauge is not None
            else None
        )
    else:
        diameter_line = (
            f"  Diameter            : {result.diameter_m:.3f} m ({result.diameter_in:.1f} in)"
        )
        axial_line = (
            f"  {axial_label:<19}: {result.axial_length_m:.3f} m ({result.axial_length_in:.1f} in)"
        )
        vapor_mass = inputs.vapor_mass_flow_kg_s
        liquid_mass = inputs.liquid_mass_flow_kg_s
        vapor_density = inputs.vapor_density_kg_m3
        liquid_density = inputs.liquid_density_kg_m3
        mass_unit = "kg/s"
        density_unit = "kg/m³"
        pressure_line = (
            f"  Operating pressure  : {inputs.pressure_bar_gauge:.1f} bar g"
            if inputs.pressure_bar_gauge is not None
            else None
        )

    lines = [
        f"{orientation_label} Flash Drum Sizing",
        "Isenthalpic separator — outlet stream properties define the design basis.",
        "",
        "Inputs",
        f"  Vapor mass flow     : {vapor_mass:.4f} {mass_unit}",
        f"  Liquid mass flow    : {liquid_mass:.4f} {mass_unit}",
        f"  Vapor density       : {vapor_density:.2f} {density_unit}",
        f"  Liquid density      : {liquid_density:.2f} {density_unit}",
        f"  Residence time      : {inputs.residence_time_min:.1f} min",
        f"  Liquid level        : {DEFAULT_LIQUID_LEVEL_FRACTION:.0%} (half-full)",
        f"  K-factor            : {result.k_factor_used:.4f} m/s ({result.k_factor_source})",
        f"  {'L/D' if inputs.orientation is DrumOrientation.HORIZONTAL else 'H/D'} ratio           : {inputs.l_over_d:.2f}",
        f"  Vapor area margin   : {inputs.margin:.0%}",
    ]
    if pressure_line:
        lines.append(pressure_line)
    if inputs.use_gpsa_k_factor and inputs.k_factor_applicability:
        lines.append(f"  K applicability     : {inputs.k_factor_applicability}")

    lines.extend(
        [
            "",
            "Results",
            diameter_line,
            axial_line,
            f"  Governing criterion : {result.governing_criterion}",
            f"  Max vapor velocity  : {result.max_vapor_velocity_m_s:.3f} m/s",
            f"  Actual vapor velocity: {result.actual_vapor_velocity_m_s:.3f} m/s",
            f"  D from vapor side   : {result.diameter_from_vapor_m:.3f} m",
            f"  D from liquid side  : {result.diameter_from_liquid_m:.3f} m",
            f"  Liquid height       : {result.liquid_height_m:.3f} m",
        ]
    )

    if result.minimum_vertical_height_m is not None:
        lines.append(
            f"  Min vertical height : {result.minimum_vertical_height_m:.3f} m"
        )

    return "\n".join(lines)