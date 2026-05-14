from rocket.stage import Stage


def _make_stage(fuel=1000.0, burn_rate=100.0):
    """Helper: create a simple active stage."""
    s = Stage(
        name="Test Stage",
        dry_mass=500.0,
        fuel_mass=fuel,
        thrust_sl=500_000,
        thrust_vac=600_000,
        burn_rate=burn_rate,
    )
    s.active = True
    return s


def test_normal_thrust_returned():
    s = _make_stage(fuel=1000.0, burn_rate=100.0)
    thrust = s.update(500_000, dt=1.0)
    assert thrust == 500_000


def test_no_thrust_when_inactive():
    s = _make_stage()
    s.active = False
    assert s.update(500_000, dt=1.0) == 0.0


def test_no_thrust_when_detached():
    s = _make_stage()
    s.detached = True
    assert s.update(500_000, dt=1.0) == 0.0


def test_no_thrust_when_already_empty():
    s = _make_stage(fuel=0.0)
    s.fuel_system.empty = True
    assert s.update(500_000, dt=1.0) == 0.0


def test_partial_thrust_on_last_tick():
    # Stage has only 10 kg of fuel but burn rate would consume 100 kg in 1 s.
    # Should return scaled thrust (~10%) not full thrust.
    s = _make_stage(fuel=10.0, burn_rate=100.0)
    thrust = s.update(500_000, dt=1.0)
    assert s.fuel_system.empty
    assert 0 < thrust < 500_000


def test_stage_empty_after_fuel_runs_out():
    s = _make_stage(fuel=50.0, burn_rate=100.0)
    s.update(500_000, dt=1.0)
    assert s.fuel_system.empty
