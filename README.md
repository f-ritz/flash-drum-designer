# Flash Drum Designer

**Flash Drum Designer is not a process simulator.** It does not run flash calculations, heat balances, or thermodynamic separation modeling.

It is a **preliminary mechanical sizing tool** for horizontal and vertical knockout drums. Run your process in a simulator such as Aspen Plus, take the **vapor and liquid outlet stream results** (mass flow rates and densities), add design parameters such as residence time and K-factor, and this program estimates the **drum diameter and length/height** to build.

Aspen Plus can model a **FLASH2** separator, but it does not size the vessel. Flash Drum Designer fills that gap using standard Souders-Brown and liquid-holdup correlations.

## Quick Start (Windows)

1. Open the [**Releases**](https://github.com/f-ritz/flash-drum-designer/releases) tab on GitHub.
2. Download **`FlashDrumDesigner.exe`** from the latest release.
3. Double-click the executable to launch the desktop app.
4. Enter outlet stream data from your simulation (or click **Load Example** to try a sample case).
5. Click **Calculate**. A PDF sizing report is saved automatically in the same folder as the EXE.

No Python installation is required when using the packaged executable.

## What This Tool Does

- Accepts **outlet vapor and liquid** mass flow rates and densities from your converged simulation
- Sizes the drum using **Souders-Brown** vapor disengagement and **liquid holdup** for a user-specified residence time
- Supports **horizontal and vertical** orientation
- Looks up **GPSA pressure-based K-factors** (or accepts a manual K-factor)
- Applies GPSA service corrections (standard, glycol/amine, compressor suction), demister adjustment, and pressure applicability rules
- Assumes a fixed **50% liquid level** (half-full) for holdup and horizontal vapor-area sizing
- Works in **SI or US customary** units
- Exports a **PDF report** with input/result tables and a vessel schematic

## What This Tool Does Not Do

- Simulate the process or predict stream compositions
- Replace Aspen, HYSYS, or any other process simulator
- Model heat duty, feed conditions, or phase equilibrium
- Size nozzles, internals, or a complete mechanical design package

**Typical workflow:** simulate in Aspen (or similar) → copy outlet flows and densities → size the drum here → use the results for preliminary mechanical design.

## Using the Desktop App

### Getting data from Aspen Plus

After your simulation converges:

1. Open the **FLASH2** (or equivalent flash/separator) block results.
2. Read the **outlet vapor stream**: mass flow rate and density.
3. Read the **outlet liquid stream**: mass flow rate and density.
4. Enter those values in Flash Drum Designer along with your target residence time and design parameters.

The built-in **Load Example** case uses representative propane/n-butane NGL outlet data so you can verify the tool — it is not a substitute for your simulation.

### Main steps in the GUI

1. Choose **unit system** and **orientation** (horizontal or vertical).
2. Enter **outlet stream data** (vapor/liquid mass flow and density).
3. Set **design parameters**: residence time, K-factor source (GPSA table or manual), service type, demister option, L/D or H/D ratio, and vapor area margin.
4. For GPSA lookup, pick a table pressure (or enter a custom pressure) and specify whether the K-factor applies at, above, or below that pressure. The effective K-factor preview updates as you change settings.
5. Click **Calculate** to see sizing results in the results panel.

### PDF reports

| How you run the app | PDF behavior |
|---------------------|--------------|
| **Downloaded EXE** | PDF is saved automatically next to the executable when you click **Calculate**. A dialog shows the full path. Use **Save PDF Again** to write another timestamped copy. |
| **Run from source** (`py app.py`) | Click **Export PDF** after calculating to choose where to save the report. |

## Design Basis (Summary)

Sizing applies published separator correlations to simulator outlet data. The tool does not recompute the flash.

**Vapor disengagement** — Souders-Brown:

$$V_{\max} = K \sqrt{\frac{\rho_l - \rho_v}{\rho_v}}$$

Required vapor flow area includes a configurable safety margin (default **20%**). For horizontal drums, vapor area is based on roughly half the cross-section at 50% liquid level; for vertical drums, on the area above the liquid level.

**Liquid holdup** — drum volume sized for the requested residence time at 50% liquid level.

**Final dimensions** — diameter is the larger of vapor-side and liquid-side requirements; length (horizontal) or height (vertical) follows the selected L/D or H/D ratio, with vertical drums able to grow when inventory or disengagement needs require it.

Defaults: **5 min** residence time, **L/D or H/D = 4.0**, **K = 0.107 m/s** when not using GPSA lookup.

### GPSA K-factor table (gauge pressure)

| Gauge pressure (bar) | K-factor (m/s) |
|----------------------|----------------|
| 0                    | 0.107          |
| 7                    | 0.107          |
| 21                   | 0.101          |
| 42                   | 0.092          |
| 63                   | 0.083          |
| 105                  | 0.065          |

The GUI applies GPSA service multipliers, demister/no-demister rules, and pressure-relation logic (at / below / above selected pressure). See the in-app K-factor preview for the value used in your case.

### Assumptions and limitations

- Outlet properties are taken as given from your simulator
- Preliminary mechanical sizing only — confirm droplet settling, nozzles, mechanical design, and demister selection separately

## For Developers

Requires **Python 3.10+**.

```powershell
git clone https://github.com/f-ritz/flash-drum-designer.git
cd flash-drum-designer
py -m pip install -r requirements.txt
py app.py
```

### Command-line interface

```powershell
py flash_drum_sizing.py --vapor-mass 3.267 --liquid-mass 3.267 --vapor-density 79.42 --liquid-density 843.58
```

GPSA K-factor and PDF export:

```powershell
py flash_drum_sizing.py --orientation vertical --use-gpsa-k --pressure 21 --vapor-mass 3.267 --liquid-mass 3.267 --vapor-density 79.42 --liquid-density 843.58 --pdf flash_drum_report.pdf
```

Imperial units:

```powershell
py flash_drum_sizing.py --units imperial --vapor-mass 11760 --liquid-mass 11760 --vapor-density 4.96 --liquid-density 52.65
```

Run `py flash_drum_sizing.py --help` for all options.

### Build the Windows EXE

```powershell
.\build_exe.ps1
```

Output: `dist\FlashDrumDesigner.exe`. Optional icon: place `assets/icon.ico` before building.

### Tests

```powershell
py -m pytest
```

## Project Structure

```
flash-drum-designer/
├── app.py                  # PySide6 desktop GUI
├── flash_drum_sizing.py    # CLI entry point
├── build_exe.ps1           # Windows EXE build script
├── FlashDrumDesigner.spec  # PyInstaller spec
├── assets/                 # App icon (icon.ico)
├── flash_drum_designer/
│   ├── sizing.py           # Souders-Brown and holdup sizing
│   ├── k_factor.py         # GPSA K-factor lookup
│   ├── examples.py         # Sample outlet-stream case
│   ├── units.py            # Unit conversions
│   ├── paths.py            # EXE and PDF path helpers
│   ├── pdf_export.py       # PDF report generation
│   └── theme.py            # Windows 10 GUI theme
└── tests/
```

## License

Use and modify freely for engineering and academic work. Verify all results against applicable design standards before issuing for construction.