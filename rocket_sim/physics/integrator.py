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

