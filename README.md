# Flash Drum Designer

Preliminary sizing tool for **horizontal and vertical** two-phase flash drums (knockout drums / vapor-liquid separators) using outlet stream data from process simulators such as Aspen Plus **FLASH2**.

Aspen Plus does not size FLASH2 separator drums directly. This project applies two standard design criteria—**Souders-Brown vapor disengagement** and **liquid residence time**—and reports the governing drum dimensions.

## Scope

This tool models an **isenthalpic flash separator**:

- No heat duty or reboiler/condenser inputs are required
- Whatever enters the drum thermally leaves through the outlet streams you provide
- Design inputs are **outlet vapor and liquid mass flows and densities** from a converged FLASH2 simulation

## Features

- Horizontal and vertical drum orientation
- Souders-Brown sizing with manual or **GPSA pressure-based K-factor lookup**
- GPSA service corrections (standard, glycol/amine, compressor suction)
- Demister / no-demister K-factor adjustment
- Liquid holdup sizing from user-specified residence time
- SI and US customary input units
- PDF report export with input/result tables and vessel schematic
- Command-line interface and native Windows desktop GUI (PySide6)
- Unit tests for sizing equations, GPSA lookup, conversions, and PDF export

## Design Basis

### 1. Vapor Disengagement — Souders-Brown Equation

$$
V_{\max} = K \sqrt{\frac{\rho_l - \rho_v}{\rho_v}}
$$

| Symbol | Description |
|--------|-------------|
| $V_{\max}$ | Maximum allowable vapor velocity (m/s) |
| $K$ | Souders-Brown constant (m/s) |
| $\rho_l$ | Liquid density (kg/m³) |
| $\rho_v$ | Vapor density (kg/m³) |

Required vapor flow area includes a configurable safety margin (default **20%**).

| Orientation | Vapor flow area basis |
|-------------|----------------------|
| Horizontal | ~50% of vessel cross-section (half-full liquid level) |
| Vertical | Full vessel cross-section above the liquid level |

### 2. Liquid Holdup — Residence Time

- Default residence time: **5 minutes**
- Fixed liquid level: **50%** (half-full) — used for holdup volume and horizontal vapor-area sizing
- Default L/D or H/D ratio: **4.0**

### 3. Final Dimensions

- **Diameter** is the larger of the vapor-side and liquid-side requirements
- **Length** (horizontal) or **height** (vertical) follows the selected L/D or H/D ratio
- Vertical drums may increase height when liquid inventory plus minimum vapor disengagement exceeds H/D sizing

## Assumptions and Limitations

- Isenthalpic operation with no heat transfer sizing
- Preliminary mechanical sizing only
- Simplified liquid-level geometry
- Final design still requires droplet settling checks, nozzle sizing, mechanical design, and vendor demister confirmation

## K-Factor Guidance (GPSA)

Enable GPSA lookup with operating gauge pressure, or enter K manually.

| Gauge Pressure (bar) | K-factor (m/s) |
|----------------------|----------------|
| 0                    | 0.107          |
| 7                    | 0.107          |
| 21                   | 0.101          |
| 42                   | 0.092          |
| 63                   | 0.083          |
| 105                  | 0.065          |

GPSA adjustment rules:

1. Start at $K = 0.107$ at 7 bar gauge; subtract 0.003 for each additional 7 bar above 7 bar.
2. For glycol or amine services, multiply $K$ by 0.6–0.8.
3. For vertical separators without mesh pads, use roughly half the table values.
4. For compressor suction scrubbers and expander inlet separators, multiply $K$ by 0.7–0.8.

## Installation

Requires Python 3.10+.

```powershell
git clone <repository-url>
cd flash-drum-designer
py -m pip install -r requirements.txt
```

## Usage

### Desktop GUI

```powershell
py app.py
```

Select orientation, unit system, outlet stream data, and design parameters. Enable GPSA K-factor lookup to size K from operating pressure. After calculating, use **Export PDF** to save a formatted report with a 50% liquid-level schematic.

### Windows EXE

1. Place your icon file at `assets/icon.ico`
2. Build the executable:

```powershell
.\build_exe.ps1
```

3. Run `dist\FlashDrumDesigner.exe`

When running the packaged EXE:

- PDF reports are saved automatically next to the executable when you click **Calculate**
- A dialog shows the full path where the PDF was saved
- The results panel also displays the saved PDF path
- **Save PDF Again** writes another timestamped copy in the same folder

### Command Line

#### SI example (horizontal)

```powershell
py flash_drum_sizing.py --vapor-mass 3.267 --liquid-mass 3.267 --vapor-density 79.42 --liquid-density 843.58
```

#### Vertical drum with GPSA K-factor

```powershell
py flash_drum_sizing.py --orientation vertical --use-gpsa-k --pressure 21 --vapor-mass 3.267 --liquid-mass 3.267 --vapor-density 79.42 --liquid-density 843.58
```

#### US customary units

```powershell
py flash_drum_sizing.py --units imperial --vapor-mass 11760 --liquid-mass 11760 --vapor-density 4.96 --liquid-density 52.65
```

#### Export to PDF

```powershell
py flash_drum_sizing.py --vapor-mass 3.267 --liquid-mass 3.267 --vapor-density 79.42 --liquid-density 843.58 --pdf flash_drum_report.pdf
```

#### Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--vapor-mass` | Vapor mass flow (kg/s or lb/hr) | Required |
| `--liquid-mass` | Liquid mass flow (kg/s or lb/hr) | Required |
| `--vapor-density` | Vapor density (kg/m³ or lb/ft³) | Required |
| `--liquid-density` | Liquid density (kg/m³ or lb/ft³) | Required |
| `--units` | `si` or `imperial` | `si` |
| `--orientation` | `horizontal` or `vertical` | `horizontal` |
| `--residence-time` | Liquid residence time (minutes) | 5.0 |
| `--k-factor` | Manual K-factor (m/s) | 0.107 |
| `--use-gpsa-k` | Enable GPSA K-factor lookup | off |
| `--pressure` | Gauge pressure (bar g or psig) | — |
| `--service` | `standard`, `glycol_amine`, `compressor_suction` | `standard` |
| `--service-multiplier` | Override GPSA service multiplier | — |
| `--no-demister` | Apply no-demister K reduction | off |
| `--l-over-d` | L/D or H/D ratio | 4.0 |
| `--margin` | Vapor area safety margin | 1.20 |
| `--pdf` | Export sizing report to PDF path | — |

### Tests

```powershell
py -m pytest
```

## Project Structure

```
flash-drum-designer/
├── app.py                  # PySide6 desktop application
├── build_exe.ps1           # Windows EXE build script
├── FlashDrumDesigner.spec  # PyInstaller spec (icon + packaging)
├── assets/
│   └── icon.ico            # Your custom app/EXE icon (you provide this)
├── flash_drum_sizing.py    # CLI entry point
├── flash_drum_designer/
│   ├── __init__.py
│   ├── sizing.py           # Horizontal and vertical sizing
│   ├── k_factor.py         # GPSA K-factor lookup
│   ├── units.py            # Unit conversions
│   ├── paths.py            # EXE/output path helpers
│   └── pdf_export.py       # PDF report generation
├── tests/
│   ├── test_sizing.py
│   ├── test_k_factor.py
│   ├── test_units.py
│   └── test_pdf_export.py
├── requirements.txt
└── README.md
```

## Data Source

After your FLASH2 simulation converges, copy the **outlet** vapor and liquid **mass flow rates** and **densities** from the stream results. Because the drum is treated as isenthalpic, those outlet values are the complete thermal and material design basis.

## License

Use and modify freely for engineering and academic work. Verify all results against applicable design standards before issuing for construction.