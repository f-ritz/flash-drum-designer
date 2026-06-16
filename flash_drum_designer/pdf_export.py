"""PDF report export for flash drum sizing results."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from reportlab.graphics.shapes import Drawing, Line, Rect, String
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Flowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from flash_drum_designer.sizing import (
    DEFAULT_LIQUID_LEVEL_FRACTION,
    DrumOrientation,
    FlashDrumInputs,
    FlashDrumResult,
)
from flash_drum_designer.units import UnitSystem, bar_gauge_to_psig, kg_m3_to_lb_ft3, kg_s_to_lb_hr, m_to_ft

LIQUID_FILL = colors.HexColor("#4a90d9")
VESSEL_STROKE = colors.HexColor("#333333")
LIGHT_TEXT = colors.HexColor("#555555")


def _input_rows(inputs: FlashDrumInputs, unit_system: UnitSystem) -> list[tuple[str, str]]:
    if unit_system is UnitSystem.IMPERIAL:
        rows = [
            ("Vapor mass flow", f"{kg_s_to_lb_hr(inputs.vapor_mass_flow_kg_s):.4f} lb/hr"),
            ("Liquid mass flow", f"{kg_s_to_lb_hr(inputs.liquid_mass_flow_kg_s):.4f} lb/hr"),
            ("Vapor density", f"{kg_m3_to_lb_ft3(inputs.vapor_density_kg_m3):.2f} lb/ft³"),
            ("Liquid density", f"{kg_m3_to_lb_ft3(inputs.liquid_density_kg_m3):.2f} lb/ft³"),
        ]
        if inputs.pressure_bar_gauge is not None:
            rows.append(
                ("Operating pressure", f"{bar_gauge_to_psig(inputs.pressure_bar_gauge):.1f} psig")
            )
    else:
        rows = [
            ("Vapor mass flow", f"{inputs.vapor_mass_flow_kg_s:.4f} kg/s"),
            ("Liquid mass flow", f"{inputs.liquid_mass_flow_kg_s:.4f} kg/s"),
            ("Vapor density", f"{inputs.vapor_density_kg_m3:.2f} kg/m³"),
            ("Liquid density", f"{inputs.liquid_density_kg_m3:.2f} kg/m³"),
        ]
        if inputs.pressure_bar_gauge is not None:
            rows.append(("Operating pressure", f"{inputs.pressure_bar_gauge:.1f} bar g"))

    axial_label = "H/D ratio" if inputs.orientation is DrumOrientation.VERTICAL else "L/D ratio"
    rows.extend(
        [
            ("Orientation", inputs.orientation.value.capitalize()),
            ("Residence time", f"{inputs.residence_time_min:.1f} min"),
            ("Liquid level (design)", f"{DEFAULT_LIQUID_LEVEL_FRACTION:.0%} (half-full)"),
            ("K-factor", f"{inputs.effective_k_factor:.4f} m/s"),
            ("K-factor source", inputs.k_factor_source),
            (
                "K applicability",
                inputs.k_factor_applicability if inputs.use_gpsa_k_factor else "Manual entry",
            ),
            (axial_label, f"{inputs.l_over_d:.2f}"),
            ("Vapor area margin", f"{inputs.margin:.0%}"),
            ("Demister", "Yes" if inputs.has_demister else "No"),
            ("Service type", inputs.service_type.value.replace("_", " ")),
        ]
    )
    return rows


def _result_rows(
    inputs: FlashDrumInputs,
    result: FlashDrumResult,
    unit_system: UnitSystem,
) -> list[tuple[str, str]]:
    axial_label = "Height" if inputs.orientation is DrumOrientation.VERTICAL else "Length"

    if unit_system is UnitSystem.IMPERIAL:
        rows = [
            ("Diameter", f"{result.diameter_ft:.3f} ft ({result.diameter_in:.1f} in)"),
            (axial_label, f"{result.axial_length_ft:.3f} ft ({result.axial_length_in:.1f} in)"),
        ]
    else:
        rows = [
            ("Diameter", f"{result.diameter_m:.3f} m ({result.diameter_in:.1f} in)"),
            (axial_label, f"{result.axial_length_m:.3f} m ({result.axial_length_in:.1f} in)"),
        ]

    rows.extend(
        [
            ("Governing criterion", result.governing_criterion),
            ("Max vapor velocity", f"{result.max_vapor_velocity_m_s:.3f} m/s"),
            ("Actual vapor velocity", f"{result.actual_vapor_velocity_m_s:.3f} m/s"),
            ("Diameter from vapor side", f"{result.diameter_from_vapor_m:.3f} m"),
            ("Diameter from liquid side", f"{result.diameter_from_liquid_m:.3f} m"),
            ("Liquid inventory height", f"{result.liquid_height_m:.3f} m"),
        ]
    )

    if result.minimum_vertical_height_m is not None:
        rows.append(
            ("Minimum vertical height", f"{result.minimum_vertical_height_m:.3f} m")
        )

    return rows


def _styled_table(rows: list[tuple[str, str]], header: str) -> Table:
    table = Table([[header, ""]] + [[label, value] for label, value in rows], colWidths=[2.4 * inch, 4.0 * inch])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0078d4")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("SPAN", (0, 0), (-1, 0)),
                ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (1, 1), (1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#d0d0d0")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


def _build_vessel_drawing(inputs: FlashDrumInputs, result: FlashDrumResult) -> Drawing:
    """Schematic showing the fixed 50% liquid level design assumption."""
    width = 280
    height = 140 if inputs.orientation is DrumOrientation.HORIZONTAL else 180
    margin = 20
    drawing = Drawing(width, height)

    if inputs.orientation is DrumOrientation.HORIZONTAL:
        vessel_width = width - 2 * margin
        vessel_height = 70
        origin_x = margin
        origin_y = 30
        liquid_height = vessel_height * DEFAULT_LIQUID_LEVEL_FRACTION

        vessel = Rect(origin_x, origin_y, vessel_width, vessel_height, strokeColor=VESSEL_STROKE, fillColor=None)
        liquid = Rect(
            origin_x,
            origin_y,
            vessel_width,
            liquid_height,
            strokeColor=colors.transparent,
            fillColor=LIQUID_FILL,
        )
        level_line = Line(
            origin_x,
            origin_y + liquid_height,
            origin_x + vessel_width,
            origin_y + liquid_height,
            strokeColor=VESSEL_STROKE,
            strokeDashArray=[4, 3],
        )
        title = String(width / 2, height - 10, "Horizontal drum — 50% liquid level", textAnchor="middle", fontSize=9)
        d_label = String(origin_x + vessel_width / 2, origin_y - 12, f"D = {result.diameter_m:.3f} m", textAnchor="middle", fontSize=8)
        l_label = String(origin_x - 8, origin_y + vessel_height / 2, f"L = {result.axial_length_m:.3f} m", textAnchor="end", fontSize=8)
        note = String(
            origin_x + vessel_width + 8,
            origin_y + liquid_height / 2,
            "Liquid",
            fontSize=8,
            fillColor=LIGHT_TEXT,
        )
        vapor_note = String(
            origin_x + vessel_width + 8,
            origin_y + liquid_height + (vessel_height - liquid_height) / 2,
            "Vapor",
            fontSize=8,
            fillColor=LIGHT_TEXT,
        )
        for shape in (vessel, liquid, level_line, title, d_label, l_label, note, vapor_note):
            drawing.add(shape)
        return drawing

    vessel_width = 90
    vessel_height = height - 50
    origin_x = (width - vessel_width) / 2
    origin_y = 25
    liquid_height = vessel_height * DEFAULT_LIQUID_LEVEL_FRACTION

    vessel = Rect(origin_x, origin_y, vessel_width, vessel_height, strokeColor=VESSEL_STROKE, fillColor=None)
    liquid = Rect(
        origin_x,
        origin_y,
        vessel_width,
        liquid_height,
        strokeColor=colors.transparent,
        fillColor=LIQUID_FILL,
    )
    level_line = Line(
        origin_x,
        origin_y + liquid_height,
        origin_x + vessel_width,
        origin_y + liquid_height,
        strokeColor=VESSEL_STROKE,
        strokeDashArray=[4, 3],
    )
    title = String(width / 2, height - 10, "Vertical drum — 50% liquid volume", textAnchor="middle", fontSize=9)
    d_label = String(origin_x + vessel_width / 2, origin_y - 12, f"D = {result.diameter_m:.3f} m", textAnchor="middle", fontSize=8)
    h_label = String(origin_x + vessel_width + 10, origin_y + vessel_height / 2, f"H = {result.axial_length_m:.3f} m", fontSize=8)
    level_label = String(
        origin_x - 10,
        origin_y + liquid_height,
        "50% level",
        textAnchor="end",
        fontSize=8,
        fillColor=LIGHT_TEXT,
    )
    for shape in (vessel, liquid, level_line, title, d_label, h_label, level_label):
        drawing.add(shape)
    return drawing


class VesselDrawingFlowable(Flowable):
    """Render a reportlab graphics drawing inside a Platypus story."""

    def __init__(self, drawing: Drawing, width: float, height: float) -> None:
        super().__init__()
        self.drawing = drawing
        self.width = width
        self.height = height

    def wrap(self, avail_width: float, avail_height: float) -> tuple[float, float]:
        return self.width, self.height

    def draw(self) -> None:
        self.drawing.drawOn(self.canv, 0, 0)


def export_result_pdf(
    file_path: str | Path,
    inputs: FlashDrumInputs,
    result: FlashDrumResult,
    *,
    unit_system: UnitSystem = UnitSystem.SI,
) -> Path:
    """Write a formatted sizing report to PDF."""
    output_path = Path(file_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontSize=18,
        spaceAfter=6,
        textColor=colors.HexColor("#1f1f1f"),
    )
    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontSize=10,
        textColor=LIGHT_TEXT,
        spaceAfter=12,
    )
    note_style = ParagraphStyle(
        "ReportNote",
        parent=styles["Normal"],
        fontSize=9,
        textColor=LIGHT_TEXT,
        spaceAfter=8,
    )

    orientation_label = inputs.orientation.value.capitalize()
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
        title=f"{orientation_label} Flash Drum Sizing Report",
    )

    story = [
        Paragraph("Flash Drum Sizing Report", title_style),
        Paragraph(
            f"{orientation_label} isenthalpic FLASH2 separator &mdash; generated "
            f"{datetime.now().strftime('%Y-%m-%d %H:%M')}",
            subtitle_style,
        ),
        Paragraph(
            "Design basis: outlet stream properties with no heat duty. "
            f"Liquid level is fixed at <b>{DEFAULT_LIQUID_LEVEL_FRACTION:.0%}</b> "
            "(half-full) for holdup and horizontal vapor-area calculations.",
            note_style,
        ),
        _styled_table(_input_rows(inputs, unit_system), "Inputs"),
        Spacer(1, 0.2 * inch),
        _styled_table(_result_rows(inputs, result, unit_system), "Results"),
        Spacer(1, 0.25 * inch),
        Paragraph("Vessel Schematic", styles["Heading3"]),
        Spacer(1, 0.05 * inch),
    ]

    drawing = _build_vessel_drawing(inputs, result)
    flowable = VesselDrawingFlowable(drawing, width=280, height=180)
    story.append(flowable)
    story.append(
        Paragraph(
            "Preliminary sizing only. Verify with detailed droplet settling, nozzle sizing, "
            "mechanical design, and vendor demister data before construction.",
            note_style,
        )
    )

    doc.build(story)
    return output_path