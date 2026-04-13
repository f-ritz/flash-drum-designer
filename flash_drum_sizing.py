# -*- coding: utf-8 -*-
"""
Created on Sun Apr 12 14:24:38 2026

@author: Fritz
"""


import numpy as np

def size_horizontal_flash_drum(
    vapor_mass_flow_kg_s: float,
    liquid_mass_flow_kg_s: float,
    vapor_density_kg_m3: float,
    liquid_density_kg_m3: float,
    residence_time_min: float = 5.0,
    K_factor: float = 0.107,          # m/s (conservative for horizontal with demister)
    L_over_D: float = 4.0,            # Typical L/D ratio
    margin: float = 1.20              # 20% safety margin
):
    """
    Sizes a horizontal flash drum based on Aspen FLASH2 results.
    
    Returns: diameter (m), length (m), vapor velocity (m/s)
    """
    
    # Convert mass flows to volumetric flows
    Qv = vapor_mass_flow_kg_s / vapor_density_kg_m3      # m³/s  (vapor)
    Ql = liquid_mass_flow_kg_s / liquid_density_kg_m3    # m³/s  (liquid)
    
    # 1. Vapor side - Souders-Brown
    Vmax = K_factor * np.sqrt((liquid_density_kg_m3 - vapor_density_kg_m3) / vapor_density_kg_m3)
    
    # Required vapor area (with margin)
    Av_required = Qv / Vmax * margin
    
    # Minimum diameter from vapor side (assuming ~50-60% of cross-section for vapor)
    D_min_vapor = np.sqrt(4 * Av_required / (np.pi * 0.5))   # assuming half full roughly
    
    # 2. Liquid side - Residence time
    liquid_holdup_volume = Ql * (residence_time_min * 60)    # m³ (at half full)
    total_volume_required = liquid_holdup_volume * 2         # for ~50% liquid level
    
    # From volume and L/D ratio
    D_from_volume = (4 * total_volume_required / (np.pi * L_over_D)) ** (1/3)
    
    # Take the larger diameter to satisfy both criteria
    D = max(D_min_vapor, D_from_volume)
    
    # Calculate actual length
    L = L_over_D * D
    
    # Actual vapor velocity
    vapor_area_actual = (np.pi * D**2 / 4) * 0.5   # approximate vapor space
    actual_vapor_velocity = Qv / vapor_area_actual
    
    print("=== Horizontal Flash Drum Sizing ===")
    print(f"Vapor flow      : {vapor_mass_flow_kg_s:.4f} kg/s")
    print(f"Liquid flow     : {liquid_mass_flow_kg_s:.4f} kg/s")
    print(f"Residence time  : {residence_time_min} min")
    print(f"Calculated Diameter : {D:.3f} m ({D*39.37:.1f} inches)")
    print(f"Calculated Length   : {L:.3f} m ({L*39.37:.1f} inches)")
    print(f"L/D ratio       : {L/D:.2f}")
    print(f"Max vapor velocity  : {Vmax:.3f} m/s")
    print(f"Actual vapor velocity: {actual_vapor_velocity:.3f} m/s")
    print(f"Margin applied  : {margin:.0%}")
    
    return D, L, actual_vapor_velocity


# ========================== COMMAND LINE INTERFACE ==========================
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Size a horizontal flash drum based on vapor and liquid flows from Aspen FLASH2."
    )

    parser.add_argument("--vapor-mass",     type=float, required=True,  help="Vapor mass flow rate (kg/s)")
    parser.add_argument("--liquid-mass",    type=float, required=True,  help="Liquid mass flow rate (kg/s)")
    parser.add_argument("--vapor-density",  type=float, required=True,  help="Vapor density (kg/m³)")
    parser.add_argument("--liquid-density", type=float, required=True,  help="Liquid density (kg/m³)")

    parser.add_argument("--residence-time", type=float, default=5.0,    help="Liquid residence time (minutes) [default: 5.0]")
    parser.add_argument("--k-factor",       type=float, default=0.107,  help="Souders-Brown K-factor (m/s) [default: 0.107]")
    parser.add_argument("--l-over-d",       type=float, default=4.0,    help="Length to Diameter ratio [default: 4.0]")
    parser.add_argument("--margin",         type=float, default=1.20,   help="Safety margin on vapor area [default: 1.20]")

    args = parser.parse_args()

    size_horizontal_flash_drum(
        vapor_mass_flow_kg_s = args.vapor_mass,
        liquid_mass_flow_kg_s = args.liquid_mass,
        vapor_density_kg_m3 = args.vapor_density,
        liquid_density_kg_m3 = args.liquid_density,
        residence_time_min = args.residence_time,
        K_factor = args.k_factor,
        L_over_D = args.l_over_d,
        margin = args.margin
    )