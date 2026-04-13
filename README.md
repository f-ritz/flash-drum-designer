# Flash Drum Designer

Tool for sizing Aspen Plus's FLASH2 separator drums.
Aspen Plus has a FLASH2 unit which to my knowledge does not have sizing built-in, so I wrote my own in Python to help with my senior design project.
I figured I'd post it here lest anybody else have the same problem.

Currently it's just a .py file, though I want to eventually make it more easy to use with a GUI.

## Working Principles

This script provides a **quick preliminary sizing** of a **horizontal two-phase flash drum** (also called a knockout drum or vapor-liquid separator) based on results from a process simulator (e.g., Aspen FLASH2).

The goal of a flash drum is to:
- Separate vapor and liquid phases efficiently
- Prevent liquid carryover into the vapor outlet
- Provide sufficient liquid residence time for degassing and level control

The script sizes the drum using two main criteria and takes the **more conservative (larger)** diameter:

### 1. Vapor Velocity – Souders-Brown Equation

To minimize liquid droplet entrainment in the vapor, the maximum allowable vapor velocity is calculated with the **Souders-Brown equation**:

$$
V_{\max} = K \sqrt{\frac{\rho_l - \rho_v}{\rho_v}}
$$

where:
- $V_{\max}$ = maximum allowable vapor velocity (m/s)
- $K$ = Souders-Brown constant (empirical) — default `0.107 m/s` (conservative value for horizontal drum **with demister/mesh pad**)
- $\rho_l$ = liquid density (kg/m³)
- $\rho_v$ = vapor density (kg/m³)

A **20% safety margin** is applied by default when calculating the required vapor flow area.

**Why this equation?**  
It is a widely used empirical correlation (originally from Mott Souders and George Brown) that ensures droplets can settle out of the rising vapor stream under gravity.

### 2. Liquid Holdup – Residence Time

The liquid section must provide enough volume so the liquid has adequate time to disengage dissolved gas and allow stable level control.

The script assumes:
- **5 minutes** liquid residence time (default, common for many flash drums)
- Approximately **50%** liquid level (half-full drum)
- Typical **L/D ratio = 4.0** (common range for horizontal separators is 3–6)

The required diameter from the liquid side is calculated from the total vessel volume needed for the holdup.

### Final Sizing Logic

- Calculate minimum diameter required by **vapor disengagement** (Souders-Brown)
- Calculate minimum diameter required by **liquid residence time**
- Take the **larger** of the two diameters
- Apply the chosen **L/D ratio** to determine vessel length
- Report actual vapor velocity (should be well below $V_{\max}$)

### Assumptions and Limitations

- Horizontal drum orientation
- Roughly 50% vapor / 50% liquid cross-sectional area (simplified)
- Includes a demister (hence the chosen K-factor)
- Preliminary sizing only — final design should include detailed droplet settling calculations, nozzle sizing, mechanical design, and vendor confirmation

### Typical Design Guidelines Used

- Liquid residence time: 3–10 minutes (5 min is a good starting point)
- L/D ratio: 3–6 (4 is very common)
- K-factor: 0.107 m/s for horizontal separators with wire mesh demister at moderate pressure

### Saunders-Brown Empirical Constants

The **K-factor** is an empirical constant that depends on vessel orientation, presence of a mist eliminator (demister/mesh pad), operating pressure, and service type.

The **GPSA Engineering Data Book** provides the following recommended K-values (in m/s) for **vertical drums with horizontal mesh pads**:

| Gauge Pressure (bar) | K-factor (m/s) |
|----------------------|----------------|
| 0                    | 0.107          |
| 7                    | 0.107          |
| 21                   | 0.101          |
| 42                   | 0.092          |
| 63                   | 0.083          |
| 105                  | 0.065          |

**GPSA Adjustment Rules:**
1. Start with **K = 0.107** at 7 bar gauge. Subtract **0.003** for every additional 7 bar above 7 bar.
2. For **glycol or amine solutions**, multiply the K-value by **0.6 – 0.8**.
3. For **vertical separators without mesh pads**, use approximately **one-half** of the above values.
4. For **compressor suction scrubbers** and **expander inlet separators**, multiply K by **0.7 – 0.8**.

> **Note for horizontal drums:**  
> The values above are officially given for vertical vessels. For **horizontal flash drums with a mesh pad** (the case handled by this script), many engineers use the same table as a conservative starting point. The script defaults to `K_factor = 0.107` m/s, which is a safe, commonly used conservative value for moderate-pressure horizontal separators equipped with a demister.

### Why the Default K = 0.107?

- It matches the GPSA recommendation at low-to-moderate pressure (≤ 7 bar g).
- It includes a built-in safety margin for horizontal flow and typical mesh pad performance.
- You can lower it at higher pressures or raise it slightly if you have detailed vendor data for your specific demister.

### How to Choose K in Practice

- Low pressure flash drums (< 10 bar): `K = 0.107`
- High pressure (> 40 bar): Reduce according to the GPSA table or rule.
- Foaming or viscous services (amine/glycol): Apply the 0.6–0.8 multiplier.
- No demister: Use ~0.05–0.06 m/s (roughly half).

Always verify the final design with detailed droplet settling calculations, vendor mist eliminator data, and mechanical considerations.

## How to Use

When you run a FLASH2 drum in Aspen and flip to the stream results, it'll have calculated the densities and mass flowrates of the vapor and liquid fractions leaving the drum for you.
This information is essential to this script.
By default, K = 0.107 and residence time = 5 minutes, so you do not need to enter those manually if you don't wish to change them.

### Running from Command Line

Open a terminal in the folder containing `flash_drum_sizing.py` and use the following commands:

#### On Windows (PowerShell or Command Prompt)
```powershell
py flash_drum_sizing.py --vapor-mass 3.267 --liquid-mass 3.267 --vapor-density 79.42 --liquid-density 843.58
```
#### On Linux / macOS

```bash
python flash_drum_sizing.py --vapor-mass 3.267 --liquid-mass 3.267 --vapor-density 79.42 --liquid-density 843.58
```

#### Available arguments

Argument,Description,Default,Required
--vapor-mass,Vapor mass flow rate (kg/s),-,Yes
--liquid-mass,Liquid mass flow rate (kg/s),-,Yes
--vapor-density,Vapor density (kg/m³),-,Yes
--liquid-density,Liquid density (kg/m³),-,Yes
--residence-time,Liquid residence time (minutes),5.0,No
--k-factor,Souders-Brown K-factor (m/s),0.107,No
--l-over-d,Length / Diameter ratio,4.0,No
--margin,Safety margin on vapor area,1.20,No

#### Basic example using test values
```powershell
py flash_drum_sizing.py --vapor-mass 3.267 --liquid-mass 3.267 --vapor-density 79.42 --liquid-density 843.58
```

#### Custom example with different residence time and K-factor
```powershell
py flash_drum_sizing.py --vapor-mass 8.5 --liquid-mass 4.2 --vapor-density 45.3 --liquid-density 720 --residence-time 6 --k-factor 0.095
```
