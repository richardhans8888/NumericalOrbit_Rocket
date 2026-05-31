"""
Tests for the vehicle and orbit data definitions.
Ensures all vehicles are properly defined and the physics make sense.
"""
import pytest
from mission.vehicle_database import VEHICLES
from mission.orbit_targets import ORBITS

REQUIRED_STAGE_FIELDS = {"dry_mass", "propellant_mass", "thrust_vac", "burn_time"}
REQUIRED_VEHICLE_FIELDS = {"name", "stages", "fairing", "cross_sectional_area", "drag_coefficient"}


@pytest.mark.parametrize("vehicle_id", list(VEHICLES.keys()))
def test_vehicle_has_required_fields(vehicle_id):
    v = VEHICLES[vehicle_id]
    for field in REQUIRED_VEHICLE_FIELDS:
        assert field in v, f"{vehicle_id} missing field: {field}"


@pytest.mark.parametrize("vehicle_id", list(VEHICLES.keys()))
def test_vehicle_has_at_least_one_stage(vehicle_id):
    assert len(VEHICLES[vehicle_id]["stages"]) >= 1


@pytest.mark.parametrize("vehicle_id", list(VEHICLES.keys()))
def test_all_stages_have_required_fields(vehicle_id):
    for i, stage in enumerate(VEHICLES[vehicle_id]["stages"]):
        for field in REQUIRED_STAGE_FIELDS:
            assert field in stage, f"{vehicle_id} stage {i} missing field: {field}"


@pytest.mark.parametrize("vehicle_id", list(VEHICLES.keys()))
def test_stage_masses_are_positive(vehicle_id):
    for stage in VEHICLES[vehicle_id]["stages"]:
        assert stage["dry_mass"] > 0
        assert stage["propellant_mass"] > 0


@pytest.mark.parametrize("vehicle_id", list(VEHICLES.keys()))
def test_stage_has_thrust(vehicle_id):
    for stage in VEHICLES[vehicle_id]["stages"]:
        # At least vacuum thrust must be positive (stage 1 may have sl thrust = 0 for upper stages)
        assert stage["thrust_vac"] > 0


@pytest.mark.parametrize("vehicle_id", list(VEHICLES.keys()))
def test_fairing_jettison_altitude_in_atmosphere(vehicle_id):
    fairing = VEHICLES[vehicle_id]["fairing"]
    # Fairing jettison should happen below the Karman line (100km) or just above
    assert fairing["jettison_altitude"] > 50_000  # at least 50km up
    assert fairing["jettison_altitude"] < 200_000  # not unrealistically high


def test_pslv_has_four_stages():
    assert len(VEHICLES["PSLV_C37"]["stages"]) == 4


def test_falcon9_has_two_stages():
    assert len(VEHICLES["FALCON_9"]["stages"]) == 2


@pytest.mark.parametrize("orbit_id", list(ORBITS.keys()))
def test_orbit_has_required_fields(orbit_id):
    o = ORBITS[orbit_id]
    assert "target_altitude_m" in o
    assert "target_velocity_m_s" in o
    assert "name" in o


@pytest.mark.parametrize("orbit_id", list(ORBITS.keys()))
def test_orbit_altitude_is_above_atmosphere(orbit_id):
    alt = ORBITS[orbit_id]["target_altitude_m"]
    assert alt > 100_000, f"{orbit_id} orbit altitude is below the Karman line"


@pytest.mark.parametrize("orbit_id", list(ORBITS.keys()))
def test_orbit_velocity_is_realistic(orbit_id):
    vel = ORBITS[orbit_id]["target_velocity_m_s"]
    # All orbital velocities should be between 3 km/s (deep space) and 11 km/s (LEO)
    assert 3_000 < vel < 11_000, f"{orbit_id} velocity {vel} m/s seems unrealistic"
