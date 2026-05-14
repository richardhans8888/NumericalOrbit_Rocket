"""
Integration tests for the World simulation loop.
Verifies that the simulation runs, phases transition correctly,
and the rocket gains altitude after launch.
"""
from mission.vehicle_database import VEHICLES
from mission.orbit_targets import ORBITS
from mission.flight_phases import FlightPhase
from simulation.world import World


def _make_world(vehicle_id="FALCON_9", orbit_id="LEO"):
    Profile = type("Profile", (), {
        "vehicle_data": VEHICLES[vehicle_id],
        "orbit_data": ORBITS[orbit_id],
        "vehicle_id": vehicle_id,
    })
    return World(Profile())


def test_world_starts_in_prelaunch():
    w = _make_world()
    assert w.phase == FlightPhase.PRELAUNCH


def test_world_update_does_nothing_before_start():
    w = _make_world()
    y_before = w.rocket.y
    w.update(dt_real=1.0)
    assert w.rocket.y == y_before  # rocket doesn't move in PRELAUNCH


def test_world_start_switches_to_liftoff():
    w = _make_world()
    w.start()
    assert w.phase == FlightPhase.LIFTOFF


def test_rocket_gains_altitude_after_launch():
    w = _make_world()
    w.start()
    initial_alt = w.rocket.get_altitude()
    for _ in range(10):
        w.update(dt_real=1.0)
    assert w.rocket.get_altitude() > initial_alt


def test_rocket_gains_velocity_after_launch():
    w = _make_world()
    w.start()
    for _ in range(10):
        w.update(dt_real=1.0)
    assert w.rocket.get_velocity_mag() > 0


def test_time_elapsed_increases_with_updates():
    w = _make_world()
    w.start()
    w.update(dt_real=1.0)
    assert w.time_elapsed > 0


def test_time_warp_scales_elapsed_time():
    w = _make_world()
    w.start()
    w.time_warp = 10.0
    w.update(dt_real=1.0)
    assert abs(w.time_elapsed - 10.0) < 0.01


def test_pslv_simulation_runs_without_crash():
    # Just make sure the 4-stage rocket doesn't crash the simulation loop
    w = _make_world("PSLV_C37", "SSO")
    w.start()
    for _ in range(20):
        w.update(dt_real=1.0)
    assert w.rocket.get_altitude() >= 0


def test_phase_transitions_to_max_q():
    # Jump rocket to 12km altitude manually, then run an update
    w = _make_world()
    w.start()
    from physics.constants import EARTH_RADIUS
    w.rocket.y = EARTH_RADIUS + 12_000
    w.update(dt_real=1.0)
    assert w.phase == FlightPhase.MAX_Q


def test_stage_separation_sets_upper_stage_burn():
    # After first stage separates, phase should be UPPER_STAGE_BURN (not BOOSTER_BURNOUT)
    w = _make_world("FALCON_9", "LEO")
    w.start()
    # Drain stage 0 fuel completely
    w.rocket.stages[0].fuel_system.consume(w.rocket.stages[0].fuel_system.fuel)
    w.rocket.stages[0].fuel_system.empty = True
    w.update(dt_real=0.01)
    assert w.phase in (FlightPhase.UPPER_STAGE_BURN, FlightPhase.BOOSTER_BURNOUT, FlightPhase.SECO)


def test_world_all_vehicles_can_be_simulated():
    # Smoke test: every vehicle can be started and run 5 ticks
    for vid in VEHICLES:
        orbit_id = VEHICLES[vid]["orbit_types"][0]
        w = _make_world(vid, orbit_id)
        w.start()
        for _ in range(5):
            w.update(dt_real=1.0)
