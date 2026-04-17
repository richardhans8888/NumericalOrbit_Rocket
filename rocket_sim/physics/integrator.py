# physics/integrator.py
"""
Numerical integration using Forward Euler method.

This is a first-order explicit method for solving ODEs:
    v(t+dt) = v(t) + a(t) * dt
    x(t+dt) = x(t) + v(t) * dt

While simple, Forward Euler is sufficient for real-time simulation
at small timesteps. For higher accuracy, Runge-Kutta 4 (RK4) could
be implemented in a future iteration.
"""

def update_velocity(vx, vy, ax, ay, dt):
    """
    Update velocity components using Forward Euler integration.
    
    Args:
        vx, vy: current velocity (m/s)
        ax, ay: current acceleration (m/s^2)
        dt: timestep (seconds)
    
    Returns:
        tuple (vx_new, vy_new)
    """
    return vx + ax * dt, vy + ay * dt

def update_position(x, y, vx, vy, dt):
    """
    Update position components using Forward Euler integration.
    
    Args:
        x, y: current position (meters)
        vx, vy: current velocity (m/s)
        dt: timestep (seconds)
    
    Returns:
        tuple (x_new, y_new)
    """
    return x + vx * dt, y + vy * dt


def rk4_step_state(state, dt, deriv_fn):
    """
    Generic RK4 step for a state vector (list/tuple of floats).

    Args:
        state: iterable of floats
        dt: timestep (s)
        deriv_fn: function(state) -> derivative vector (same length)

    Returns:
        list of floats (next state)
    """
    y0 = list(state)
    k1 = deriv_fn(y0)
    y1 = [y0[i] + 0.5 * dt * k1[i] for i in range(len(y0))]
    k2 = deriv_fn(y1)
    y2 = [y0[i] + 0.5 * dt * k2[i] for i in range(len(y0))]
    k3 = deriv_fn(y2)
    y3 = [y0[i] + dt * k3[i] for i in range(len(y0))]
    k4 = deriv_fn(y3)
    return [y0[i] + (dt / 6.0) * (k1[i] + 2.0 * k2[i] + 2.0 * k3[i] + k4[i]) for i in range(len(y0))]
