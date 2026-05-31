"""
Tests for the Rocket class — stage management, mass tracking, satellite mode.
"""
import math
from rocket.rocket import Rocket
from mission.vehicle_database import VEHICLES


def _make_rocket(vehicle_id="FALCON_9"):
    return Rocket(VEHICLES[vehicle_id])


def test_rocket_starts_at_earth_surface():
    from physics.constants import EARTH_RADIUS
    r = _make_rocket()
    assert r.x == 0.0
    assert r.y == EARTH_RADIUS


def test_rocket_starts_pointing_up():
    r = _make_rocket()
    assert abs(r.pitch_angle - math.pi / 2.0) < 1e-9


def test_rocket_initial_stage_count_falcon9():
    r = _make_rocket("FALCON_9")
    assert len(r.stages) == 2


def test_rocket_initial_stage_count_pslv():
    r = _make_rocket("PSLV_C37")
    assert len(r.stages) == 4


def test_activate_next_stage_marks_stage_active():
    r = _make_rocket()
    assert not r.stages[0].active
    r.activate_next_stage()
    assert r.stages[0].active


def test_total_mass_includes_all_stages_and_fairing():
    r = _make_rocket("FALCON_9")
    v = VEHICLES["FALCON_9"]
    expected = sum(
        s["dry_mass"] + s["propellant_mass"] for s in v["stages"]
    ) + v["fairing"]["mass"]
    assert r.get_total_mass() == expected


def test_altitude_at_start_is_zero():
    r = _make_rocket()
    assert abs(r.get_altitude()) < 1.0  # should be ~0 at surface


def test_stage_separation_increments_index():
    r = _make_rocket()
    r.activate_next_stage()
    r.stages[0].fuel_system.consume(r.stages[0].fuel_system.fuel)  # drain stage
    r.stages[0].fuel_system.empty = True
    r.separate_current_stage()
    assert r.current_stage_index == 1


def test_stage_separation_detaches_stage():
    r = _make_rocket()
    r.separate_current_stage()
    assert r.stages[0].detached


def test_stage_separation_activates_next_stage():
    r = _make_rocket()
    r.activate_next_stage()
    r.separate_current_stage()
    assert r.stages[1].active


def test_jettison_fairing_removes_it():
    r = _make_rocket()
    assert r.fairing_attached
    r.jettison_fairing()
    assert not r.fairing_attached


def test_satellite_mode_reduces_mass():
    r = _make_rocket()
    full_mass = r.get_total_mass()
    r.enter_satellite_mode(sat_mass_kg=500.0)
    assert r.get_total_mass() == 500.0
    assert r.get_total_mass() < full_mass


def test_no_thrust_force_in_satellite_mode():
    r = _make_rocket()
    r.enter_satellite_mode()
    fx, fy = r.get_thrust_force(9_000_000)
    assert fx == 0.0 and fy == 0.0


def test_update_systems_returns_event_and_thrust():
    r = _make_rocket()
    r.activate_next_stage()
    event, thrust = r.update_systems(dt=1.0, throttle_pct=1.0)
    assert thrust > 0
    assert event is None or isinstance(event, str)
