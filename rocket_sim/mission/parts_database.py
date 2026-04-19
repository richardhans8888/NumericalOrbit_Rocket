# mission/parts_database.py
"""
Rocket parts database for custom vehicle assembly.
Includes engines, fuel tanks, and fairings with pre-defined specs.
"""

ENGINES = {
    "MERLIN_1D": {
        "name": "Merlin 1D (RP-1/LOX)",
        "thrust_sl": 845000,
        "thrust_vac": 914000,
        "isp_sl": 282,
        "isp_vac": 311,
        "mass": 470,
    },
    "RD_180": {
        "name": "RD-180 (RP-1/LOX)",
        "thrust_sl": 3827000,
        "thrust_vac": 4152000,
        "isp_sl": 311,
        "isp_vac": 338,
        "mass": 5480,
    },
    "VULCAIN_2": {
        "name": "Vulcain 2 (LH2/LOX)",
        "thrust_sl": 960000,
        "thrust_vac": 1350000,
        "isp_sl": 310,
        "isp_vac": 432,
        "mass": 1800,
    },
    "RUTHERFORD": {
        "name": "Rutherford (Electric RP-1)",
        "thrust_sl": 24000,
        "thrust_vac": 26000,
        "isp_sl": 303,
        "isp_vac": 311,
        "mass": 35,
        "power_draw_kw": 12.0, # Electric pump power draw
    },
    "HM7B": {
        "name": "HM7B Upper Stage",
        "thrust_sl": 0,
        "thrust_vac": 64800,
        "isp_sl": 0,
        "isp_vac": 444,
        "mass": 165,
        "power_draw_kw": 0.0,
    },
    "MERLIN_VAC": {
        "name": "Merlin Vacuum",
        "thrust_sl": 0,
        "thrust_vac": 981000,
        "isp_sl": 0,
        "isp_vac": 348,
        "mass": 490,
        "power_draw_kw": 0.0,
    }
}

FUEL_TANKS = {
    "SMALL_TANK": {
        "name": "Small Composite Tank",
        "dry_mass": 200,
        "propellant_mass": 2000,
        "battery_capacity_kwh": 5.0,
    },
    "MEDIUM_TANK": {
        "name": "Medium Alloy Tank",
        "dry_mass": 4000,
        "propellant_mass": 50000,
        "battery_capacity_kwh": 0.0,
    },
    "LARGE_TANK": {
        "name": "Large Kerolox Tank",
        "dry_mass": 20000,
        "propellant_mass": 400000,
        "battery_capacity_kwh": 0.0,
    },
    "HEAVY_TANK": {
        "name": "Heavy Cryogenic Tank",
        "dry_mass": 30000,
        "propellant_mass": 650000,
        "battery_capacity_kwh": 0.0,
    }
}

FAIRINGS = {
    "SMALL": {
        "name": "Small Sat Fairing",
        "mass": 50,
        "jettison_altitude": 100000.0,
    },
    "STANDARD": {
        "name": "Standard Fairing",
        "mass": 1500,
        "jettison_altitude": 110000.0,
    },
    "HEAVY": {
        "name": "Heavy-lift Fairing",
        "mass": 2500,
        "jettison_altitude": 120000.0,
    }
}
