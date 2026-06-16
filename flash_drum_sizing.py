"""Command-line entry point for flash drum sizing."""

from __future__ import annotations

import argparse
import sys

from flash_drum_designer import (
    DrumOrientation,
    FlashDrumInputs,
    ServiceType,
    UnitSystem,
    export_result_pdf,
    format_result,
    size_flash_drum,
)
from flash_drum_designer.units import bar_gauge_to_psig, lb_ft3_to_kg_m3, lb_hr_to_kg_s, psig_to_bar_gauge


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Size a horizontal or vertical isenthalpic flash drum from Aspen FLASH2 "
            "vapor and liquid outlet stream data."
        )
    )
    parser.add_argument("--vapor-mass", type=float, required=True, help="Vapor mass flow")
    parser.add_argument("--liquid-mass", type=float, required=True, help="Liquid mass flow")
    parser.add_argument("--vapor-density", type=float, required=True, help="Vapor density")
    parser.add_argument("--liquid-density", type=float, required=True, help="Liquid density")
    parser.add_argument(
        "--units",
        choices=("si", "imperial"),
        default="si",
        help="Input units: si (kg/s, kg/m³, bar g) or imperial (lb/hr, lb/ft³, psig)",
    )
    parser.add_argument(
        "--orientation",
        choices=("horizontal", "vertical"),
        default="horizontal",
        help="Drum orientation [default: horizontal]",
    )
    parser.add_argument(
        "--residence-time",
        type=float,
        default=5.0,
        help="Liquid residence time (minutes) [default: 5.0]",
    )
    parser.add_argument(
        "--k-factor",
        type=float,
        default=None,
        help="Manual Souders-Brown K-factor (m/s). Defaults to 0.107 when GPSA is off.",
    )
    parser.add_argument(
        "--use-gpsa-k",
        action="store_true",
        help="Look up K-factor from GPSA using operating pressure",
    )
    parser.add_argument(
        "--pressure",
        type=float,
        default=None,
        help="Operating gauge pressure (bar g for SI, psig for imperial)",
    )
    parser.add_argument(
        "--service",
        choices=("standard", "glycol_amine", "compressor_suction"),
        default="standard",
        help="GPSA service correction [default: standard]",
    )
    parser.add_argument(
        "--service-multiplier",
        type=float,
        default=None,
        help="Optional override for GPSA service multiplier",
    )
    parser.add_argument(
        "--no-demister",
        action="store_true",
        help="Apply no-demister K-factor reduction",
    )
    parser.add_argument(
        "--l-over-d",
        type=float,
        default=4.0,
        help="Length-to-diameter or height-to-diameter ratio [default: 4.0]",
    )
    parser.add_argument(
        "--margin",
        type=float,
        default=1.20,
        help="Safety margin on required vapor area [default: 1.20]",
    )
    parser.add_argument(
        "--pdf",
        type=str,
        default=None,
        metavar="PATH",
        help="Export sizing report to PDF at the given path",
    )
    return parser


def _convert_inputs(args: argparse.Namespace) -> tuple[FlashDrumInputs, UnitSystem]:
    unit_system = UnitSystem(args.units)

    if unit_system is UnitSystem.IMPERIAL:
        vapor_mass_flow_kg_s = lb_hr_to_kg_s(args.vapor_mass)
        liquid_mass_flow_kg_s = lb_hr_to_kg_s(args.liquid_mass)
        vapor_density_kg_m3 = lb_ft3_to_kg_m3(args.vapor_density)
        liquid_density_kg_m3 = lb_ft3_to_kg_m3(args.liquid_density)
        pressure_bar_gauge = (
            psig_to_bar_gauge(args.pressure) if args.pressure is not None else None
        )
    else:
        vapor_mass_flow_kg_s = args.vapor_mass
        liquid_mass_flow_kg_s = args.liquid_mass
        vapor_density_kg_m3 = args.vapor_density
        liquid_density_kg_m3 = args.liquid_density
        pressure_bar_gauge = args.pressure

    inputs = FlashDrumInputs(
        vapor_mass_flow_kg_s=vapor_mass_flow_kg_s,
        liquid_mass_flow_kg_s=liquid_mass_flow_kg_s,
        vapor_density_kg_m3=vapor_density_kg_m3,
        liquid_density_kg_m3=liquid_density_kg_m3,
        orientation=DrumOrientation(args.orientation),
        residence_time_min=args.residence_time,
        k_factor=args.k_factor if args.k_factor is not None else 0.107,
        use_gpsa_k_factor=args.use_gpsa_k,
        pressure_bar_gauge=pressure_bar_gauge,
        service_type=ServiceType(args.service),
        service_multiplier=args.service_multiplier,
        has_demister=not args.no_demister,
        l_over_d=args.l_over_d,
        margin=args.margin,
    )
    return inputs, unit_system


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        inputs, unit_system = _convert_inputs(args)
        result = size_flash_drum(inputs)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(format_result(inputs, result, unit_system=unit_system))

    if args.pdf:
        pdf_path = export_result_pdf(args.pdf, inputs, result, unit_system=unit_system)
        print(f"\nPDF report written to: {pdf_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())