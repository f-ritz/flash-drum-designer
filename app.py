"""Desktop GUI for horizontal and vertical flash drum sizing."""

from __future__ import annotations

import sys
from enum import Enum
from pathlib import Path
from typing import TypeVar

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from flash_drum_designer import (
    DrumOrientation,
    FlashDrumInputs,
    FlashDrumResult,
    ServiceType,
    UnitSystem,
    export_result_pdf,
    format_result,
    size_flash_drum,
)
from flash_drum_designer.examples import EXAMPLES, FlashDrumExample
from flash_drum_designer.k_factor import (
    KFactorMode,
    PressureRelation,
    gpsa_pressure_presets,
    preview_k_factor,
)
from flash_drum_designer.paths import build_default_pdf_path, get_icon_path, is_frozen
from flash_drum_designer.theme import apply_windows10_theme
from flash_drum_designer.units import bar_gauge_to_psig, lb_ft3_to_kg_m3, lb_hr_to_kg_s, psig_to_bar_gauge

CUSTOM_GPSA_PRESET_KEY = "custom"

E = TypeVar("E", bound=Enum)


def _enum_from_combo(combo: QComboBox, enum_cls: type[E]) -> E:
    """PySide6 stores StrEnum user data as plain strings in itemData()."""
    data = combo.currentData()
    if isinstance(data, enum_cls):
        return data
    if isinstance(data, str):
        return enum_cls(data)
    raise ValueError(f"Invalid selection for {enum_cls.__name__}.")


def _set_combo_enum(combo: QComboBox, value: Enum) -> None:
    index = combo.findData(value.value)
    if index < 0:
        raise ValueError(f"Combo box has no entry for {value!r}.")
    combo.setCurrentIndex(index)


class FlashDrumWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Flash Drum Designer")
        self.setMinimumSize(900, 720)
        self._last_inputs: FlashDrumInputs | None = None
        self._last_result: FlashDrumResult | None = None
        self._last_pdf_path: Path | None = None
        self._block_k_updates = False
        self._build_ui()
        self._update_unit_labels()
        self._update_k_factor_controls()

    def _build_ui(self) -> None:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.setCentralWidget(scroll)

        container = QWidget()
        scroll.setWidget(container)
        root = QVBoxLayout(container)
        root.setContentsMargins(24, 20, 24, 24)
        root.setSpacing(12)

        title = QLabel("Flash Drum Designer")
        title.setObjectName("titleLabel")
        root.addWidget(title)

        subtitle_text = (
            "Preliminary sizing for isenthalpic FLASH2 separators. Outlet vapor and liquid "
            "stream data define the design basis — no heat duty is modeled. "
            "Liquid level is fixed at 50% (half-full)."
        )
        if is_frozen():
            subtitle_text += (
                " PDF reports are saved automatically in the same folder as this application."
            )
        subtitle = QLabel(subtitle_text)
        subtitle.setObjectName("subtitleLabel")
        subtitle.setWordWrap(True)
        root.addWidget(subtitle)

        header_separator = QFrame()
        header_separator.setObjectName("headerSeparator")
        header_separator.setFrameShape(QFrame.Shape.HLine)
        header_separator.setFrameShadow(QFrame.Shadow.Plain)
        root.addWidget(header_separator)

        content = QHBoxLayout()
        content.setSpacing(16)
        root.addLayout(content)

        left_column = QVBoxLayout()
        left_column.setSpacing(12)
        content.addLayout(left_column, stretch=3)

        config_group = QGroupBox("Configuration")
        config_form = QFormLayout(config_group)
        config_form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        config_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.unit_system = QComboBox()
        self.unit_system.addItem("SI (kg/s, kg/m³, bar g)", UnitSystem.SI.value)
        self.unit_system.addItem("US Customary (lb/hr, lb/ft³, psig)", UnitSystem.IMPERIAL.value)
        self.unit_system.currentIndexChanged.connect(self._update_unit_labels)

        self.orientation = QComboBox()
        self.orientation.addItem("Horizontal", DrumOrientation.HORIZONTAL.value)
        self.orientation.addItem("Vertical", DrumOrientation.VERTICAL.value)
        self.orientation.currentIndexChanged.connect(self._update_unit_labels)

        config_form.addRow("Unit system", self.unit_system)
        config_form.addRow("Orientation", self.orientation)
        left_column.addWidget(config_group)

        stream_group = QGroupBox("Outlet Stream Data")
        self.stream_form = QFormLayout(stream_group)
        self.stream_form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        self.stream_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.example_info = QLabel()
        self.example_info.setObjectName("exampleInfoLabel")
        self.example_info.setWordWrap(True)
        self.example_info.hide()

        self.vapor_mass = self._spinbox(0.0, 1_000_000.0, 4, 3.267)
        self.liquid_mass = self._spinbox(0.0, 1_000_000.0, 4, 3.267)
        self.vapor_density = self._spinbox(0.0, 5000.0, 3, 79.42)
        self.liquid_density = self._spinbox(0.0, 5000.0, 3, 843.58)

        self.vapor_mass_label = QLabel()
        self.liquid_mass_label = QLabel()
        self.vapor_density_label = QLabel()
        self.liquid_density_label = QLabel()

        self.stream_form.addRow(self.example_info)
        self.stream_form.addRow(self.vapor_mass_label, self.vapor_mass)
        self.stream_form.addRow(self.liquid_mass_label, self.liquid_mass)
        self.stream_form.addRow(self.vapor_density_label, self.vapor_density)
        self.stream_form.addRow(self.liquid_density_label, self.liquid_density)
        left_column.addWidget(stream_group)

        design_group = QGroupBox("Design Parameters")
        design_form = QFormLayout(design_group)
        design_form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        design_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.residence_time = self._spinbox(0.1, 60.0, 1, 5.0)

        self.k_factor_mode = QComboBox()
        self.k_factor_mode.addItem("GPSA table (from pressure)", KFactorMode.GPSA.value)
        self.k_factor_mode.addItem("Manual entry", KFactorMode.MANUAL.value)
        self.k_factor_mode.currentIndexChanged.connect(self._update_k_factor_controls)

        self.gpsa_pressure_preset = QComboBox()
        for preset in gpsa_pressure_presets():
            self.gpsa_pressure_preset.addItem(preset.label, preset.pressure_bar_gauge)
        self.gpsa_pressure_preset.addItem("Custom pressure...", CUSTOM_GPSA_PRESET_KEY)
        self.gpsa_pressure_preset.setCurrentIndex(1)
        self.gpsa_pressure_preset.currentIndexChanged.connect(self._on_gpsa_preset_changed)

        self.pressure = self._spinbox(0.0, 5000.0, 2, 7.0)
        self.pressure_label = QLabel("Operating pressure (bar g)")
        self.pressure.valueChanged.connect(self._refresh_k_factor_preview)

        self.pressure_relation = QComboBox()
        self.pressure_relation.addItem(
            "At selected / operating pressure",
            PressureRelation.AT.value,
        )
        self.pressure_relation.addItem(
            "For systems below selected pressure",
            PressureRelation.LESS_THAN.value,
        )
        self.pressure_relation.addItem(
            "For systems above selected pressure",
            PressureRelation.GREATER_THAN.value,
        )
        self.pressure_relation.currentIndexChanged.connect(self._refresh_k_factor_preview)

        self.k_factor = self._spinbox(0.01, 1.0, 4, 0.107)

        self.k_factor_preview = QLabel()
        self.k_factor_preview.setObjectName("kFactorPreview")
        self.k_factor_preview.setWordWrap(True)

        self.service_type = QComboBox()
        self.service_type.addItem("Standard", ServiceType.STANDARD.value)
        self.service_type.addItem("Glycol / amine", ServiceType.GLYCOL_AMINE.value)
        self.service_type.addItem("Compressor suction", ServiceType.COMPRESSOR_SUCTION.value)
        self.service_type.currentIndexChanged.connect(self._refresh_k_factor_preview)

        self.has_demister = QCheckBox("Wire-mesh demister installed")
        self.has_demister.setChecked(True)
        self.has_demister.toggled.connect(self._refresh_k_factor_preview)

        self.l_over_d = self._spinbox(1.0, 10.0, 1, 4.0)
        self.l_over_d_label = QLabel("L/D ratio")

        self.margin = self._spinbox(1.0, 2.0, 2, 1.20)

        self.gpsa_preset_label = QLabel("GPSA pressure")
        self.pressure_relation_label = QLabel("K-factor applies when")
        self.manual_k_label = QLabel("Manual K-factor (m/s)")

        design_form.addRow("Residence time (min)", self.residence_time)
        design_form.addRow("K-factor source", self.k_factor_mode)
        design_form.addRow(self.gpsa_preset_label, self.gpsa_pressure_preset)
        design_form.addRow(self.pressure_label, self.pressure)
        design_form.addRow(self.pressure_relation_label, self.pressure_relation)
        design_form.addRow("Effective K-factor", self.k_factor_preview)
        design_form.addRow(self.manual_k_label, self.k_factor)
        design_form.addRow("Service type", self.service_type)
        design_form.addRow(self.has_demister)
        design_form.addRow(self.l_over_d_label, self.l_over_d)
        design_form.addRow("Vapor area margin", self.margin)
        left_column.addWidget(design_group)

        button_row = QHBoxLayout()
        button_row.addStretch()

        self.load_example_button = QPushButton("Load Example")
        self.load_example_button.clicked.connect(self._on_load_example)
        button_row.addWidget(self.load_example_button)

        self.calculate_button = QPushButton("Calculate")
        self.calculate_button.setObjectName("primaryButton")
        self.calculate_button.setDefault(True)
        self.calculate_button.clicked.connect(self._on_calculate)
        self.calculate_button.setMinimumWidth(140)
        button_row.addWidget(self.calculate_button)

        self.export_button = QPushButton("Save PDF Again" if is_frozen() else "Export PDF")
        self.export_button.clicked.connect(self._on_export_pdf)
        self.export_button.setEnabled(False)
        if is_frozen():
            self.export_button.setToolTip("Save another PDF copy next to the executable.")
        button_row.addWidget(self.export_button)

        self.reset_button = QPushButton("Reset Defaults")
        self.reset_button.clicked.connect(self._on_reset)
        button_row.addWidget(self.reset_button)

        left_column.addLayout(button_row)

        results_group = QGroupBox("Sizing Results")
        results_layout = QVBoxLayout(results_group)

        self.results_view = QTextEdit()
        self.results_view.setReadOnly(True)
        self.results_view.setMinimumHeight(320)
        self.results_view.setPlaceholderText("Enter outlet stream data and click Calculate.")
        results_layout.addWidget(self.results_view)

        content.addWidget(results_group, stretch=4)

    @staticmethod
    def _spinbox(
        minimum: float,
        maximum: float,
        decimals: int,
        default: float,
    ) -> QDoubleSpinBox:
        spinbox = QDoubleSpinBox()
        spinbox.setRange(minimum, maximum)
        spinbox.setDecimals(decimals)
        spinbox.setValue(default)
        spinbox.setMinimumWidth(180)
        spinbox.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.NoButtons)
        spinbox.setKeyboardTracking(True)
        return spinbox

    def _current_unit_system(self) -> UnitSystem:
        return _enum_from_combo(self.unit_system, UnitSystem)

    def _current_orientation(self) -> DrumOrientation:
        return _enum_from_combo(self.orientation, DrumOrientation)

    def _current_k_factor_mode(self) -> KFactorMode:
        return _enum_from_combo(self.k_factor_mode, KFactorMode)

    def _pressure_bar_gauge(self) -> float:
        if self._current_unit_system() is UnitSystem.IMPERIAL:
            return psig_to_bar_gauge(self.pressure.value())
        return self.pressure.value()

    def _set_pressure_from_bar(self, pressure_bar_gauge: float) -> None:
        if self._current_unit_system() is UnitSystem.IMPERIAL:
            self.pressure.setValue(bar_gauge_to_psig(pressure_bar_gauge))
        else:
            self.pressure.setValue(pressure_bar_gauge)

    def _select_gpsa_preset_for_pressure(self, pressure_bar_gauge: float) -> None:
        for index in range(self.gpsa_pressure_preset.count()):
            preset_value = self.gpsa_pressure_preset.itemData(index)
            if isinstance(preset_value, float) and abs(preset_value - pressure_bar_gauge) < 0.05:
                self.gpsa_pressure_preset.setCurrentIndex(index)
                return
        custom_index = self.gpsa_pressure_preset.findData(CUSTOM_GPSA_PRESET_KEY)
        if custom_index >= 0:
            self.gpsa_pressure_preset.setCurrentIndex(custom_index)

    def _on_gpsa_preset_changed(self) -> None:
        if self._block_k_updates:
            return

        preset_value = self.gpsa_pressure_preset.currentData()
        if isinstance(preset_value, float):
            self._block_k_updates = True
            self._set_pressure_from_bar(preset_value)
            self.pressure.setEnabled(False)
            self._block_k_updates = False
        else:
            self.pressure.setEnabled(True)

        self._refresh_k_factor_preview()

    def _update_k_factor_controls(self) -> None:
        use_gpsa = self._current_k_factor_mode() is KFactorMode.GPSA

        self.gpsa_preset_label.setVisible(use_gpsa)
        self.gpsa_pressure_preset.setVisible(use_gpsa)
        self.pressure_label.setVisible(use_gpsa)
        self.pressure.setVisible(use_gpsa)
        self.pressure_relation_label.setVisible(use_gpsa)
        self.pressure_relation.setVisible(use_gpsa)
        self.manual_k_label.setVisible(not use_gpsa)
        self.k_factor.setVisible(not use_gpsa)

        if use_gpsa:
            self._on_gpsa_preset_changed()
        else:
            self.pressure.setEnabled(False)

        self._refresh_k_factor_preview()

    def _refresh_k_factor_preview(self) -> None:
        if self._block_k_updates:
            return

        mode = self._current_k_factor_mode()
        pressure_bar_gauge = self._pressure_bar_gauge() if mode is KFactorMode.GPSA else None
        manual_k = self.k_factor.value() if mode is KFactorMode.MANUAL else None

        try:
            effective_k, source, base_k, applicability = preview_k_factor(
                mode=mode,
                pressure_bar_gauge=pressure_bar_gauge,
                manual_k_factor=manual_k,
                service_type=_enum_from_combo(self.service_type, ServiceType),
                has_demister=self.has_demister.isChecked(),
                pressure_relation=_enum_from_combo(self.pressure_relation, PressureRelation),
            )
        except ValueError as exc:
            self.k_factor_preview.setText(f"K-factor unavailable: {exc}")
            return

        if mode is KFactorMode.GPSA and base_k is not None:
            self.k_factor_preview.setText(
                f"{effective_k:.4f} m/s\n"
                f"Table K = {base_k:.4f} m/s\n"
                f"{applicability}\n"
                f"{source}"
            )
        else:
            self.k_factor_preview.setText(f"{effective_k:.4f} m/s\n{source}")

    def _update_unit_labels(self) -> None:
        orientation = self._current_orientation()
        if self._current_unit_system() is UnitSystem.IMPERIAL:
            self.vapor_mass_label.setText("Vapor mass flow (lb/hr)")
            self.liquid_mass_label.setText("Liquid mass flow (lb/hr)")
            self.vapor_density_label.setText("Vapor density (lb/ft³)")
            self.liquid_density_label.setText("Liquid density (lb/ft³)")
            self.pressure_label.setText("Operating pressure (psig)")
        else:
            self.vapor_mass_label.setText("Vapor mass flow (kg/s)")
            self.liquid_mass_label.setText("Liquid mass flow (kg/s)")
            self.vapor_density_label.setText("Vapor density (kg/m³)")
            self.liquid_density_label.setText("Liquid density (kg/m³)")
            self.pressure_label.setText("Operating pressure (bar g)")

        self.l_over_d_label.setText("H/D ratio" if orientation is DrumOrientation.VERTICAL else "L/D ratio")
        self._refresh_k_factor_preview()

    def _apply_example(self, example: FlashDrumExample) -> None:
        self._block_k_updates = True

        _set_combo_enum(self.orientation, example.orientation)

        if self._current_unit_system() is UnitSystem.IMPERIAL:
            self.vapor_mass.setValue(example.vapor_mass_lb_hr)
            self.liquid_mass.setValue(example.liquid_mass_lb_hr)
            self.vapor_density.setValue(example.vapor_density_lb_ft3)
            self.liquid_density.setValue(example.liquid_density_lb_ft3)
        else:
            self.vapor_mass.setValue(example.vapor_mass_flow_kg_s)
            self.liquid_mass.setValue(example.liquid_mass_flow_kg_s)
            self.vapor_density.setValue(example.vapor_density_kg_m3)
            self.liquid_density.setValue(example.liquid_density_kg_m3)

        self.residence_time.setValue(example.residence_time_min)
        _set_combo_enum(self.k_factor_mode, KFactorMode.GPSA)
        _set_combo_enum(self.pressure_relation, PressureRelation.AT)
        self._select_gpsa_preset_for_pressure(example.pressure_bar_gauge)
        self._set_pressure_from_bar(example.pressure_bar_gauge)
        self.pressure.setEnabled(
            self.gpsa_pressure_preset.currentData() == CUSTOM_GPSA_PRESET_KEY
        )
        _set_combo_enum(self.service_type, example.service_type)
        self.has_demister.setChecked(example.has_demister)
        self.l_over_d.setValue(example.l_over_d)
        self.margin.setValue(example.margin)

        self.example_info.setText(f"Example: {example.name} — {example.description}")
        self.example_info.show()

        self._block_k_updates = False
        self._update_k_factor_controls()

    def _on_load_example(self) -> None:
        self._apply_example(EXAMPLES[0])

    def _on_reset(self) -> None:
        self.unit_system.setCurrentIndex(0)
        self.orientation.setCurrentIndex(0)
        self._block_k_updates = True
        self.vapor_mass.setValue(3.267)
        self.liquid_mass.setValue(3.267)
        self.vapor_density.setValue(79.42)
        self.liquid_density.setValue(843.58)
        self.residence_time.setValue(5.0)
        _set_combo_enum(self.k_factor_mode, KFactorMode.GPSA)
        self.gpsa_pressure_preset.setCurrentIndex(1)
        self.pressure.setValue(7.0)
        _set_combo_enum(self.pressure_relation, PressureRelation.AT)
        self.k_factor.setValue(0.107)
        self.service_type.setCurrentIndex(0)
        self.has_demister.setChecked(True)
        self.l_over_d.setValue(4.0)
        self.margin.setValue(1.20)
        self.example_info.hide()
        self.results_view.clear()
        self._last_inputs = None
        self._last_result = None
        self._last_pdf_path = None
        self.export_button.setEnabled(False)
        self._block_k_updates = False
        self._update_unit_labels()
        self._update_k_factor_controls()

    def _build_inputs(self) -> FlashDrumInputs:
        unit_system = self._current_unit_system()
        use_gpsa = self._current_k_factor_mode() is KFactorMode.GPSA

        if unit_system is UnitSystem.IMPERIAL:
            vapor_mass_flow_kg_s = lb_hr_to_kg_s(self.vapor_mass.value())
            liquid_mass_flow_kg_s = lb_hr_to_kg_s(self.liquid_mass.value())
            vapor_density_kg_m3 = lb_ft3_to_kg_m3(self.vapor_density.value())
            liquid_density_kg_m3 = lb_ft3_to_kg_m3(self.liquid_density.value())
        else:
            vapor_mass_flow_kg_s = self.vapor_mass.value()
            liquid_mass_flow_kg_s = self.liquid_mass.value()
            vapor_density_kg_m3 = self.vapor_density.value()
            liquid_density_kg_m3 = self.liquid_density.value()

        pressure_bar_gauge = self._pressure_bar_gauge() if use_gpsa else None

        return FlashDrumInputs(
            vapor_mass_flow_kg_s=vapor_mass_flow_kg_s,
            liquid_mass_flow_kg_s=liquid_mass_flow_kg_s,
            vapor_density_kg_m3=vapor_density_kg_m3,
            liquid_density_kg_m3=liquid_density_kg_m3,
            orientation=self._current_orientation(),
            residence_time_min=self.residence_time.value(),
            k_factor=None if use_gpsa else self.k_factor.value(),
            use_gpsa_k_factor=use_gpsa,
            pressure_bar_gauge=pressure_bar_gauge,
            pressure_relation=_enum_from_combo(self.pressure_relation, PressureRelation),
            service_type=_enum_from_combo(self.service_type, ServiceType),
            has_demister=self.has_demister.isChecked(),
            l_over_d=self.l_over_d.value(),
            margin=self.margin.value(),
        )

    def _on_calculate(self) -> None:
        try:
            inputs = self._build_inputs()
            result = size_flash_drum(inputs)
        except ValueError as exc:
            QMessageBox.warning(self, "Invalid Input", str(exc))
            return

        self._last_inputs = inputs
        self._last_result = result
        self.export_button.setEnabled(True)
        try:
            self._show_results(inputs, result)
        except Exception as exc:
            QMessageBox.critical(self, "Display Error", str(exc))
            return

        if is_frozen():
            pdf_path = self._save_pdf_report()
            if pdf_path is not None:
                self._notify_pdf_saved(pdf_path)

    def _show_results(self, inputs: FlashDrumInputs, result: FlashDrumResult) -> None:
        text = format_result(inputs, result, unit_system=self._current_unit_system())
        if self._last_pdf_path is not None:
            text += f"\n\nPDF report:\n  {self._last_pdf_path}"
        self.results_view.setPlainText(text)

    def _choose_export_path(self) -> Path | None:
        if self._last_inputs is None:
            return None

        if is_frozen():
            return build_default_pdf_path(self._last_inputs.orientation.value)

        default_name = f"flash_drum_{self._last_inputs.orientation.value}_sizing.pdf"
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Sizing Report",
            default_name,
            "PDF Files (*.pdf)",
        )
        if not file_path:
            return None

        path = Path(file_path)
        if path.suffix.lower() != ".pdf":
            path = path.with_suffix(".pdf")
        return path

    def _save_pdf_report(self) -> Path | None:
        if self._last_inputs is None or self._last_result is None:
            return None

        file_path = self._choose_export_path()
        if file_path is None:
            return None

        try:
            export_result_pdf(
                file_path,
                self._last_inputs,
                self._last_result,
                unit_system=self._current_unit_system(),
            )
        except OSError as exc:
            QMessageBox.critical(self, "Export Failed", str(exc))
            return None

        self._last_pdf_path = file_path.resolve()
        self._show_results(self._last_inputs, self._last_result)
        return self._last_pdf_path

    def _notify_pdf_saved(self, pdf_path: Path) -> None:
        QMessageBox.information(
            self,
            "PDF Saved",
            "Sizing report saved next to the application:\n\n"
            f"{pdf_path}",
        )

    def _on_export_pdf(self) -> None:
        if self._last_inputs is None or self._last_result is None:
            QMessageBox.information(self, "Export PDF", "Run a calculation before exporting.")
            return

        pdf_path = self._save_pdf_report()
        if pdf_path is None:
            return

        if is_frozen():
            self._notify_pdf_saved(pdf_path)
        else:
            QMessageBox.information(self, "Export Complete", f"PDF report saved to:\n{pdf_path}")

    def _assign_button_roles(self) -> None:
        self.load_example_button.setObjectName("secondaryButton")
        self.export_button.setObjectName("secondaryButton")
        self.reset_button.setObjectName("secondaryButton")


def _apply_app_icon(app: QApplication) -> None:
    icon_path = get_icon_path()
    if icon_path is not None:
        app.setWindowIcon(QIcon(str(icon_path)))


def main() -> int:
    app = QApplication(sys.argv)
    apply_windows10_theme(app)
    _apply_app_icon(app)
    window = FlashDrumWindow()
    window._assign_button_roles()
    icon_path = get_icon_path()
    if icon_path is not None:
        window.setWindowIcon(QIcon(str(icon_path)))
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())