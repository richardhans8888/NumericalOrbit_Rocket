# physics/integrator.py

def update_velocity(vx, vy, ax, ay, dt):
    """Update velocity using acceleration and timestep."""
    return vx + ax * dt, vy + ay * dt

def update_position(x, y, vx, vy, dt):
    """Update position using velocity and timestep."""
    return x + vx * dt, y + vy * dt
