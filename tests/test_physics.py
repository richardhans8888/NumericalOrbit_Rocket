import math
from physics.gravity import compute_gravity_vector
from physics.drag import compute_drag_force, get_air_density
from physics.constants import EARTH_RADIUS, ATMOSPHERE_BOUNDARY


def test_gravity_points_toward_origin():
    # Rocket sitting directly above Earth on the Y axis
    ax, ay = compute_gravity_vector(0.0, EARTH_RADIUS)
    assert ax == 0.0
    assert ay < 0.0  # must pull downward


def test_gravity_magnitude_at_surface_approx_9_8():
    ax, ay = compute_gravity_vector(0.0, EARTH_RADIUS)
    mag = math.sqrt(ax**2 + ay**2)
    assert 9.5 < mag < 10.0


def test_gravity_at_origin_returns_zero():
    # Guard against division by zero
    ax, ay = compute_gravity_vector(0.0, 0.0)
    assert ax == 0.0 and ay == 0.0


def test_gravity_weaker_at_higher_altitude():
    _, ay_low = compute_gravity_vector(0.0, EARTH_RADIUS)
    _, ay_high = compute_gravity_vector(0.0, EARTH_RADIUS + 400_000)
    assert abs(ay_high) < abs(ay_low)


def test_no_drag_above_atmosphere():
    drag = compute_drag_force(8000.0, ATMOSPHERE_BOUNDARY + 1, 0.4, 10.0)
    assert drag == 0.0


def test_drag_increases_with_speed():
    slow = compute_drag_force(100.0, 0.0, 0.4, 10.0)
    fast = compute_drag_force(1000.0, 0.0, 0.4, 10.0)
    assert fast > slow


def test_air_density_decreases_with_altitude():
    rho_low = get_air_density(0.0)
    rho_high = get_air_density(50_000.0)
    assert rho_low > rho_high > 0.0
