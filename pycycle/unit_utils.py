"""Unit system helpers for pyCycle."""

from __future__ import annotations
import math

UNIT_SYSTEMS = {
    "ENG": {
        "temperature": "degR",
        "pressure": "lbf/inch**2",
        "mass_flow": "lbm/s",
        "enthalpy": "Btu/lbm",
        "entropy": "Btu/(lbm*degR)",
        "velocity": "ft/s",
        "area": "inch**2",
        "density": "lbm/ft**3",
        "power": "hp",
        "torque": "ft*lbf",
        "force": "lbf",
        "specific_heat": "Btu/(lbm*degR)",
        "gas_constant": "Btu/(lbm*degR)",
        "enthalpy_flow": "Btu/s",
    },
    "SI": {
        "temperature": "degK",
        "pressure": "Pa",
        "mass_flow": "kg/s",
        "enthalpy": "J/kg",
        "entropy": "J/(kg*degK)",
        "velocity": "m/s",
        "area": "m**2",
        "density": "kg/m**3",
        "power": "W",
        "torque": "N*m",
        "force": "N",
        "specific_heat": "J/(kg*degK)",
        "gas_constant": "J/(kg*degK)",
        "enthalpy_flow": "W",
    },
}

STD_DAY = {
    "ENG": {"T": 518.67, "P": 14.695951},
    "SI": {"T": 288.15, "P": 101325.0},
}

MASS_FLOW_VEL_TO_FORCE = {
    "ENG": 1.0 / 32.174,
    "SI": 1.0,
}

ENTHALPY_FLOW_TO_POWER = {
    "ENG": 1.4148532,
    "SI": 1.0,
}

POWER_PER_RPM_TO_TORQUE = {
    "ENG": 5252.113122032546,
    "SI": 60.0 / (2.0 * math.pi),
}


def get_unit(var_type: str, unit_system: str = "ENG") -> str:
    """Return the unit string for a variable type in a unit system."""
    return UNIT_SYSTEMS[unit_system][var_type]
