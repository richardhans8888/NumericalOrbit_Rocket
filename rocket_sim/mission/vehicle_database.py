# mission/vehicle_database.py
"""
Satellite launch vehicle database.
All vehicles are real-world satellite launchers with approximate specs.
Values sourced from publicly available aerospace references.
"""

VEHICLES = {
    "FALCON_9": {
        "name": "Falcon 9 Block 5",
        "manufacturer": "SpaceX",
        "country": "USA",
        "description": "Partially reusable medium-lift launch vehicle. Workhorse for commercial satellite deployment.",
        "payload_leo_kg": 22800,
        "payload_geo_kg": 8300,
        "orbit_types": ["LEO", "GTO", "SSO"],
        "icon_char": "F9",
        "stages": [
            {
                "name": "Stage 1 (Merlin 9x)",
                "dry_mass": 22200,
                "propellant_mass": 411000,
                "thrust_sl": 7607000,
                "thrust_vac": 8227000,
                "burn_time": 162.0,
                "engine_count": 9,
            },
            {
                "name": "Stage 2 (Merlin Vac)",
                "dry_mass": 4000,
                "propellant_mass": 111500,
                "thrust_sl": 0,
                "thrust_vac": 934000,
                "burn_time": 397.0,
                "engine_count": 1,
            }
        ],
        "fairing": {
            "mass": 1900,
            "jettison_altitude": 115000.0
        },
        "cross_sectional_area": 10.5,
        "drag_coefficient": 0.4
    },

    "ATLAS_V": {
        "name": "Atlas V 401",
        "manufacturer": "ULA",
        "country": "USA",
        "description": "Reliable expendable launch vehicle. High mission success rate for government/commercial payloads.",
        "payload_leo_kg": 18850,
        "payload_geo_kg": 8900,
        "orbit_types": ["LEO", "GTO", "MEO"],
        "icon_char": "AV",
        "stages": [
            {
                "name": "Atlas CCB (RD-180)",
                "dry_mass": 21000,
                "propellant_mass": 284000,
                "thrust_sl": 3827000,
                "thrust_vac": 4152000,
                "burn_time": 253.0,
                "engine_count": 1,
            },
            {
                "name": "Centaur SEC (RL-10)",
                "dry_mass": 2086,
                "propellant_mass": 20830,
                "thrust_sl": 0,
                "thrust_vac": 99200,
                "burn_time": 842.0,
                "engine_count": 1,
            }
        ],
        "fairing": {
            "mass": 2127,
            "jettison_altitude": 120000.0
        },
        "cross_sectional_area": 11.4,
        "drag_coefficient": 0.4
    },

    "ARIANE_5": {
        "name": "Ariane 5 ECA",
        "manufacturer": "ArianeGroup",
        "country": "EU",
        "description": "Heavy-lift vehicle for GEO satellites. Capable of dual-payload missions.",
        "payload_leo_kg": 21000,
        "payload_geo_kg": 10500,
        "orbit_types": ["LEO", "GTO"],
        "icon_char": "A5",
        "stages": [
            {
                "name": "EPC Core + SRBs (Vulcain 2)",
                "dry_mass": 32000,
                "propellant_mass": 660000,
                "thrust_sl": 10500000,
                "thrust_vac": 13000000,
                "burn_time": 140.0,
                "engine_count": 3,
            },
            {
                "name": "ESC-A Upper (HM7B)",
                "dry_mass": 4540,
                "propellant_mass": 14900,
                "thrust_sl": 0,
                "thrust_vac": 64800,
                "burn_time": 945.0,
                "engine_count": 1,
            }
        ],
        "fairing": {
            "mass": 2400,
            "jettison_altitude": 110000.0
        },
        "cross_sectional_area": 23.0,
        "drag_coefficient": 0.4
    },

    "ELECTRON": {
        "name": "Electron",
        "manufacturer": "Rocket Lab",
        "country": "NZ/USA",
        "description": "Small-sat specialist. Electric turbopumps, carbon composite structure. SSO/LEO smallsat missions.",
        "payload_leo_kg": 300,
        "payload_geo_kg": 0,
        "orbit_types": ["LEO", "SSO"],
        "icon_char": "EL",
        "stages": [
            {
                "name": "Stage 1 (Rutherford 9x)",
                "dry_mass": 950,
                "propellant_mass": 9250,
                "thrust_sl": 162000,
                "thrust_vac": 192000,
                "burn_time": 150.0,
                "engine_count": 9,
            },
            {
                "name": "Stage 2 (Rutherford Vac)",
                "dry_mass": 250,
                "propellant_mass": 2150,
                "thrust_sl": 0,
                "thrust_vac": 25800,
                "burn_time": 330.0,
                "engine_count": 1,
            }
        ],
        "fairing": {
            "mass": 44,
            "jettison_altitude": 100000.0
        },
        "cross_sectional_area": 1.13,
        "drag_coefficient": 0.4
    },

    "SOYUZ_21B": {
        "name": "Soyuz-2.1b",
        "manufacturer": "Progress Rocket Space Centre",
        "country": "Russia",
        "description": "Upgraded Soyuz with Fregat upper stage. Primary SSO and medium-orbit satellite launcher.",
        "payload_leo_kg": 8200,
        "payload_geo_kg": 1350,
        "orbit_types": ["LEO", "SSO", "MEO"],
        "icon_char": "S2",
        "stages": [
            {
                "name": "Stage 1+2 (RD-108A/107A)",
                "dry_mass": 24400,
                "propellant_mass": 274000,
                "thrust_sl": 4140000,
                "thrust_vac": 4562000,
                "burn_time": 290.0,
                "engine_count": 4,
            },
            {
                "name": "Fregat Upper Stage (S5.92)",
                "dry_mass": 930,
                "propellant_mass": 5350,
                "thrust_sl": 0,
                "thrust_vac": 19850,
                "burn_time": 877.0,
                "engine_count": 1,
            }
        ],
        "fairing": {
            "mass": 1700,
            "jettison_altitude": 105000.0
        },
        "cross_sectional_area": 9.6,
        "drag_coefficient": 0.38
    },

    "PSLV_C37": {
        "name": "PSLV-C37 (XL)",
        "manufacturer": "ISRO",
        "country": "India",
        "description": "Record-holder: 104 satellites in one launch. India's reliable polar satellite launch vehicle.",
        "payload_leo_kg": 3800,
        "payload_geo_kg": 1400,
        "orbit_types": ["LEO", "SSO", "GTO"],
        "icon_char": "PX",
        "stages": [
            {
                "name": "PS1+S139 (Solid)",
                "dry_mass": 30200,
                "propellant_mass": 138000,
                "thrust_sl": 4846000,
                "thrust_vac": 5100000,
                "burn_time": 105.0,
                "engine_count": 1,
            },
            {
                "name": "PS2 (Vikas Liquid)",
                "dry_mass": 5300,
                "propellant_mass": 40700,
                "thrust_sl": 0,
                "thrust_vac": 799000,
                "burn_time": 158.0,
                "engine_count": 1,
            }
        ],
        "fairing": {
            "mass": 1150,
            "jettison_altitude": 115000.0
        },
        "cross_sectional_area": 8.0,
        "drag_coefficient": 0.4
    },

    "CUSTOM": {
        "name": "Custom Rocket",
        "manufacturer": "User Defined",
        "country": "International",
        "description": "Build your own rocket! Configure mass, thrust, and fuel for a custom mission profile.",
        "payload_leo_kg": 0,
        "payload_geo_kg": 0,
        "orbit_types": ["LEO", "SSO", "MEO", "GTO"],
        "icon_char": "??",
        "stages": [
            {
                "name": "Custom Stage 1",
                "dry_mass": 20000,
                "propellant_mass": 300000,
                "thrust_sl": 5000000,
                "thrust_vac": 5500000,
                "burn_time": 150.0,
                "engine_count": 1,
            },
            {
                "name": "Custom Stage 2",
                "dry_mass": 4000,
                "propellant_mass": 50000,
                "thrust_sl": 0,
                "thrust_vac": 500000,
                "burn_time": 300.0,
                "engine_count": 1,
            }
        ],
        "fairing": {
            "mass": 1500,
            "jettison_altitude": 110000.0
        },
        "cross_sectional_area": 10.0,
        "drag_coefficient": 0.4
    }
}
