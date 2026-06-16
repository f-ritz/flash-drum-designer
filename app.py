"""Desktop GUI for horizontal and vertical flash drum sizing."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
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
from flash_drum_designer.paths import build_default_pdf_path, get_icon_path, is_frozen
from flash_drum_designer.units import lb_ft3_to_kg_m3, lb_hr_to_kg_s, psig_to_bar_gauge


class FlashDrumWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Flash Drum Designer")
        self.setMinimumSize(900, 720)
        self._last_inputs: FlashDrumInputs | None = None
        self._last_result: FlashDrumResult | None = None
        self._last_pdf_path: Path | None = None
        self._build_ui()
        self._update_unit_labels()
        self._update_k_factor_state()

    def _build_ui(self) -> None:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.setCentralWidget(scroll)

        container = QWidget()
        scroll.setWidget(container)
        root = QVBoxLayout(container)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(16)

        title = QLabel("Flash Drum Designer")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setWeight(QFont.Weight.DemiBold)
        title.setFont(title_font)
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
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color: #555;")
        root.addWidget(subtitle)

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
        self.unit_system.addItem("SI (kg/s, kg/m³, bar g)", UnitSystem.SI)
        self.unit_system.addItem("US Customary (lb/hr, lb/ft³, psig)", UnitSystem.IMPERIAL)
        self.unit_system.currentIndexChanged.connect(self._update_unit_labels)

        self.orientation = QComboBox()
        self.orientation.addItem("Horizontal", DrumOrientation.HORIZONTAL)
        self.orientation.addItem("Vertical", DrumOrientation.VERTICAL)
        self.orientation.currentIndexChanged.connect(self._update_unit_labels)

        config_form.addRow("Unit system", self.unit_system)
        config_form.addRow("Orientation", self.orientation)
        left_column.addWidget(config_group)

        stream_group = QGroupBox("Outlet Stream Data")
        self.stream_form = QFormLayout(stream_group)
        self.stream_form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        self.stream_form.setLabelAlignment(Qt.AlignmentFlag.AlignRight)

        self.vapor_mass = self._spinbox(0.0, 1_000_000.0, 4, 3.267)
        self.liquid_mass = self._spinbox(0.0, 1_000_000.0, 4, 3.267)
        self.vapor_density = self._spinbox(0.0, 5000.0, 3, 79.42)
        self.liquid_density = self._spinbox(0.0, 5000.0, 3, 843.58)

        self.vapor_mass_label = QLabel()
        self.liquid_mass_label = QLabel()
        self.vapor_density_label = QLabel()
        self.liquid_density_label = QLabel()

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
        self.use_gpsa_k = QCheckBox("Use GPSA K-factor lookup")
        self.use_gpsa_k.toggled.connect(self._update_k_factor_state)

        self.pressure = self._spinbox(0.0, 5000.0, 2, 7.0)
        self.pressure_label = QLabel("Operating pressure (bar g)")

        self.k_factor = self._spinbox(0.01, 1.0, 4, 0.107)
        self.service_type = QComboBox()
        self.service_type.addItem("Standard", ServiceType.STANDARD)
        self.service_type.addItem("Glycol / amine", ServiceType.GLYCOL_AMINE)
        self.service_type.addItem("Compressor suction", ServiceType.COMPRESSOR_SUCTION)

        self.has_demister = QCheckBox("Wire-mesh demister installed")
        self.has_demister.setChecked(True)

        self.l_over_d = self._spinbox(1.0, 10.0, 1, 4.0)
        self.l_over_d_label = QLabel("L/D ratio")

        self.margin = self._spinbox(1.0, 2.0, 2, 1.20)

        design_form.addRow("Residence time (min)", self.residence_time)
        design_form.addRow(self.use_gpsa_k)
        design_form.addRow(self.pressure_label, self.pressure)
        design_form.addRow("K-factor (m/s)", self.k_factor)
        design_form.addRow("Service type", self.service_type)
        design_form.addRow(self.has_demister)
        design_form.addRow(self.l_over_d_label, self.l_over_d)
        design_form.addRow("Vapor area margin", self.margin)
        left_column.addWidget(design_group)

        button_row = QHBoxLayout()
        button_row.addStretch()

        self.calculate_button = QPushButton("Calculate")
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
        self.results_view.setPlaceholderText("Enter outlet stream data and click Calculate.")
        mono = QFont("Consolas")
        if not mono.exactMatch():
            mono = QFont("Courier New")
        self.results_view.setFont(mono)
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
        spinbox.setButtonSymbols(QDoubleSpinBox.ButtonSymbols.UpDownArrows)
        return spinbox

    def _current_unit_system(self) -> UnitSystem:
        return self.unit_system.currentData()

    def _current_orientation(self) -> DrumOrientation:
        return self.orientation.currentData()

    def _update_k_factor_state(self) -> None:
        use_gpsa = self.use_gpsa_k.isChecked()
        self.k_factor.setEnabled(not use_gpsa)
        self.pressure.setEnabled(use_gpsa)

    def _update_unit_labels(self) -> None:
        unit_system = self._current_unit_system()
        orientation = self._current_orientation()

        if unit_system is UnitSystem.IMPERIAL:
            self.vapor_mass_label.setText("Vapor mass flow (lb/hr)")
            self.liquid_mass_label.setText("Liquid mass flow (lb/hr)")
            self.vapor_density_label.setText("Vapor density (lb/ft³)")
            self.liquid_density_label.setText("Liquid density (lb/ft³)")
            self.pressure_label.setText("Operating pressure (psig)")
            self.vapor_mass.setValue(11760.0)
            self.liquid_mass.setValue(11760.0)
            self.vapor_density.setValue(4.96)
            self.liquid_density.setValue(52.65)
            self.pressure.setValue(100.0)
        else:
            self.vapor_mass_label.setText("Vapor mass flow (kg/s)")
            self.liquid_mass_label.setText("Liquid mass flow (kg/s)")
            self.vapor_density_label.setText("Vapor density (kg/m³)")
            self.liquid_density_label.setText("Liquid density (kg/m³)")
            self.pressure_label.setText("Operating pressure (bar g)")
            self.vapor_mass.setValue(3.267)
            self.liquid_mass.setValue(3.267)
            self.vapor_density.setValue(79.42)
            self.liquid_density.setValue(843.58)
            self.pressure.setValue(7.0)

        self.l_over_d_label.setText("H/D ratio" if orientation is DrumOrientation.VERTICAL else "L/D ratio")

    def _on_reset(self) -> None:
        self.unit_system.setCurrentIndex(0)
        self.orientation.setCurrentIndex(0)
        self._update_unit_labels()
        self.residence_time.setValue(5.0)
        self.use_gpsa_k.setChecked(False)
        self.k_factor.setValue(0.107)
        self.service_type.setCurrentIndex(0)
        self.has_demister.setChecked(True)
        self.l_over_d.setValue(4.0)
        self.margin.setValue(1.20)
        self.results_view.clear()
        self._last_inputs = None
        self._last_result = None
        self._last_pdf_path = None
        self.export_button.setEnabled(False)
        self._update_k_factor_state()

    def _build_inputs(self) -> FlashDrumInputs:
        unit_system = self._current_unit_system()

        if unit_system is UnitSystem.IMPERIAL:
            vapor_mass_flow_kg_s = lb_hr_to_kg_s(self.vapor_mass.value())
            liquid_mass_flow_kg_s = lb_hr_to_kg_s(self.liquid_mass.value())
            vapor_density_kg_m3 = lb_ft3_to_kg_m3(self.vapor_density.value())
            liquid_density_kg_m3 = lb_ft3_to_kg_m3(self.liquid_density.value())
            pressure_bar_gauge = (
                psig_to_bar_gauge(self.pressure.value()) if self.use_gpsa_k.isChecked() else None
            )
        else:
            vapor_mass_flow_kg_s = self.vapor_mass.value()
            liquid_mass_flow_kg_s = self.liquid_mass.value()
            vapor_density_kg_m3 = self.vapor_density.value()
            liquid_density_kg_m3 = self.liquid_density.value()
            pressure_bar_gauge = self.pressure.value() if self.use_gpsa_k.isChecked() else None

        return FlashDrumInputs(
            vapor_mass_flow_kg_s=vapor_mass_flow_kg_s,
            liquid_mass_flow_kg_s=liquid_mass_flow_kg_s,
            vapor_density_kg_m3=vapor_density_kg_m3,
            liquid_density_kg_m3=liquid_density_kg_m3,
            orientation=self._current_orientation(),
            residence_time_min=self.residence_time.value(),
            k_factor=None if self.use_gpsa_k.isChecked() else self.k_factor.value(),
            use_gpsa_k_factor=self.use_gpsa_k.isChecked(),
            pressure_bar_gauge=pressure_bar_gauge,
            service_type=self.service_type.currentData(),
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
        self._show_results(inputs, result)

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

    def _apply_style(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow, QWidget {
                background: #f3f3f3;
                color: #1f1f1f;
                font-size: 10pt;
            }
            QGroupBox {
                font-weight: 600;
                border: 1px solid #c8c8c8;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 12px;
                background: #ffffff;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
            }
            QDoubleSpinBox, QTextEdit, QComboBox {
                border: 1px solid #c8c8c8;
                border-radius: 4px;
                padding: 4px 6px;
                background: #ffffff;
            }
            QDoubleSpinBox:focus, QTextEdit:focus, QComboBox:focus {
                border: 1px solid #0078d4;
            }
            QPushButton {
                background: #0078d4;
                color: #ffffff;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: 600;
            }
            QPushButton:hover {
                background: #106ebe;
            }
            QPushButton:pressed {
                background: #005a9e;
            }
            QPushButton#secondaryButton {
                background: #e1e1e1;
                color: #1f1f1f;
            }
            QPushButton#secondaryButton:disabled {
                color: #9a9a9a;
            }
            """
        )
        self.reset_button.setObjectName("secondaryButton")
        self.export_button.setObjectName("secondaryButton")


def _apply_app_icon(app: QApplication) -> None:
    icon_path = get_icon_path()
    if icon_path is not None:
        app.setWindowIcon(QIcon(str(icon_path)))


def main() -> int:
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    _apply_app_icon(app)
    window = FlashDrumWindow()
    icon_path = get_icon_path()
    if icon_path is not None:
        window.setWindowIcon(QIcon(str(icon_path)))
    window._apply_style()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())