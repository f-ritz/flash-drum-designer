"""Representative flash drum sizing examples for testing and demos."""

from __future__ import annotations

from dataclasses import dataclass

from flash_drum_designer.k_factor import ServiceType
from flash_drum_designer.sizing import DrumOrientation
from flash_drum_designer.units import bar_gauge_to_psig, kg_m3_to_lb_ft3, kg_s_to_lb_hr


@dataclass(frozen=True)
class FlashDrumExample:
    """Outlet stream and design data for a worked example case."""

    key: str
    name: str
    description: str
    vapor_mass_flow_kg_s: float
    liquid_mass_flow_kg_s: float
    vapor_density_kg_m3: float
    liquid_density_kg_m3: float
    pressure_bar_gauge: float
    orientation: DrumOrientation = DrumOrientation.HORIZONTAL
    residence_time_min: float = 5.0
    service_type: ServiceType = ServiceType.STANDARD
    has_demister: bool = True
    l_over_d: float = 4.0
    margin: float = 1.20

    @property
    def vapor_mass_lb_hr(self) -> float:
        return kg_s_to_lb_hr(self.vapor_mass_flow_kg_s)

    @property
    def liquid_mass_lb_hr(self) -> float:
        return kg_s_to_lb_hr(self.liquid_mass_flow_kg_s)

    @property
    def vapor_density_lb_ft3(self) -> float:
        return kg_m3_to_lb_ft3(self.vapor_density_kg_m3)

    @property
    def liquid_density_lb_ft3(self) -> float:
        return kg_m3_to_lb_ft3(self.liquid_density_kg_m3)

    @property
    def pressure_psig(self) -> float:
        return bar_gauge_to_psig(self.pressure_bar_gauge)


PROPANE_BUTANE_NGL = FlashDrumExample(
    key="propane_butane_ngl",
    name="Propane / n-butane NGL flash drum",
    description=(
        "Depropanizer reflux drum at 17.2 bar g (250 psig) and 38 C. "
        "Propane-rich vapor and n-butane-rich liquid from a typical NGL "
        "fractionation train. Outlet data represent an isenthalpic FLASH2 split."
    ),
    vapor_mass_flow_kg_s=2.94,
    liquid_mass_flow_kg_s=5.18,
    vapor_density_kg_m3=52.3,
    liquid_density_kg_m3=598.0,
    pressure_bar_gauge=17.2,
    orientation=DrumOrientation.HORIZONTAL,
    residence_time_min=5.0,
    service_type=ServiceType.STANDARD,
    has_demister=True,
    l_over_d=4.0,
    margin=1.20,
)


EXAMPLES: tuple[FlashDrumExample, ...] = (PROPANE_BUTANE_NGL,)


def get_example(key: str) -> FlashDrumExample:
    for example in EXAMPLES:
        if example.key == key:
            return example
    raise KeyError(f"Unknown example: {key}")