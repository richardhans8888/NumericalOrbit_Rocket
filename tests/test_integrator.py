"""
Tests for the numerical integration methods (Euler and RK4).
These are the core computational techniques of the project.
"""
import math
from physics.integrator import update_velocity, update_position, rk4_step_state


# ── Euler integration ─────────────────────────────────────────────────────────

def test_euler_velocity_update():
    # v = v0 + a*dt  →  0 + 10 * 2 = 20
    vx, vy = update_velocity(0.0, 0.0, 10.0, 0.0, dt=2.0)
    assert vx == 20.0
    assert vy == 0.0


def test_euler_position_update():
    # x = x0 + v*dt  →  5 + 3*4 = 17
    x, y = update_position(5.0, 0.0, 3.0, 0.0, dt=4.0)
    assert x == 17.0
    assert y == 0.0


def test_euler_free_fall_position():
    # Object dropped from rest under gravity (g = 9.81 m/s^2)
    # After 1 second: y should decrease by ~9.81 m (Euler step)
    g = 9.81
    x, y = 0.0, 1000.0
    vx, vy = 0.0, 0.0
    dt = 1.0
    vx, vy = update_velocity(vx, vy, 0.0, -g, dt)
    x, y = update_position(x, y, vx, vy, dt)
    assert abs(y - (1000.0 + vy)) < 0.01  # Euler: position uses updated velocity


def test_euler_constant_velocity_no_acceleration():
    # With zero acceleration, velocity stays the same
    vx, vy = update_velocity(5.0, 3.0, 0.0, 0.0, dt=10.0)
    assert vx == 5.0
    assert vy == 3.0


# ── RK4 integration ───────────────────────────────────────────────────────────

def test_rk4_constant_velocity():
    # dx/dt = v (constant), so x(t) = x0 + v*t exactly
    def deriv(state):
        x, v = state
        return [v, 0.0]  # dx/dt = v, dv/dt = 0

    state = [0.0, 5.0]  # x=0, v=5
    result = rk4_step_state(state, dt=2.0, deriv_fn=deriv)
    assert abs(result[0] - 10.0) < 1e-10  # x = 5 * 2 = 10 exactly


def test_rk4_uniform_acceleration():
    # x(t) = 0.5 * a * t^2, with a=2, t=1 → x=1.0
    def deriv(state):
        x, v = state
        return [v, 2.0]  # dv/dt = 2 (constant acceleration)

    state = [0.0, 0.0]
    result = rk4_step_state(state, dt=1.0, deriv_fn=deriv)
    assert abs(result[0] - 1.0) < 1e-10  # x = 0.5 * 2 * 1^2 = 1.0
    assert abs(result[1] - 2.0) < 1e-10  # v = 2 * 1 = 2.0


def test_rk4_more_accurate_than_euler_for_same_step():
    # Test on circular orbit: a = -omega^2 * x (simple harmonic motion)
    # Exact solution: x(t) = cos(omega*t), exact period = 2*pi
    omega = 1.0
    dt = 0.5

    def deriv(state):
        x, v = state
        return [v, -(omega**2) * x]

    # One step from x=1, v=0
    state0 = [1.0, 0.0]

    # RK4
    rk4 = rk4_step_state(state0, dt, deriv)

    # Euler
    vx_e = state0[1] + (-(omega**2) * state0[0]) * dt
    x_e = state0[0] + state0[1] * dt

    # Exact
    x_exact = math.cos(omega * dt)

    euler_error = abs(x_e - x_exact)
    rk4_error = abs(rk4[0] - x_exact)

    assert rk4_error < euler_error, "RK4 should be more accurate than Euler"


def test_rk4_returns_same_length_as_input():
    state = [1.0, 2.0, 3.0, 4.0]
    result = rk4_step_state(state, dt=0.1, deriv_fn=lambda s: [0.0] * len(s))
    assert len(result) == len(state)
