# Rocket Launch & Orbital Simulation System

## Project Overview

This project is a **professional-grade rocket launch and orbital mechanics simulator** developed in **Python**.  
The objective is to model a real aerospace launch sequence from **pre-launch on the pad** through **ascent**, **stage separation**, and **stable satellite orbit insertion** around Earth.

The simulator is designed following real aerospace engineering principles used in modern launch systems. The architecture strictly separates:

- Physics computation (truth model)
- Vehicle systems
- Mission logic
- Visualization layer

This ensures physical correctness, scalability, and maintainability.

The simulator is **not intended as a game**, but as an engineering visualization and mission simulation environment.

---

## Primary Goals

- Simulate realistic rocket ascent from Earth.
- Model multi-stage rocket behavior.
- Perform gravity turn trajectory.
- Achieve stable circular orbit.
- Visualize mission phases professionally.
- Maintain clean modular software architecture.

---

## Core Features

### Rocket Launch Simulation
- Liftoff physics based on thrust vs gravity.
- Atmospheric ascent modeling.
- Dynamic mass reduction during fuel burn.
- Realistic acceleration profile.

### Multi-Stage Rocket System
- Booster separation.
- Stage separation events.
- Fairing jettison after atmospheric exit.
- Engine cutoff and ignition sequencing.

### Orbital Mechanics
- Two-dimensional Cartesian orbital simulation.
- Earth positioned at coordinate origin (0,0).
- Gravity modeled using inverse-square law.
- Stable orbit achieved through velocity–gravity balance.

### Flight Automation
- Gravity turn guidance.
- Max-Q throttle management.
- Automatic staging logic.
- Orbit insertion burn.
- Satellite deployment.

### Visualization
- Real-time trajectory rendering.
- Earth curvature visualization.
- Launch pad and ascent phases.
- Mission analytics interface.

---

## Launch Phases Modeled

The simulator follows real aerospace terminology:

1. Engine Ignition  
2. Liftoff  
3. Pitch Program Initiation  
4. Max-Q (Maximum Dynamic Pressure)  
5. Booster Separation  
6. Main Engine Cutoff (MECO)  
7. Stage Separation  
8. Second Engine Start (SES)  
9. Fairing Separation  
10. Orbital Insertion Burn  
11. Second Engine Cutoff (SECO)  
12. Payload Deployment  

---

---

## Architectural Philosophy

### Physics Layer
Contains pure mathematical models independent of graphics.

Responsibilities:
- gravitational force calculation
- thrust generation
- atmospheric drag
- numerical integration of motion

This layer represents the **laws of the universe**.

---

### Rocket System Layer
Represents the physical spacecraft.

Responsibilities:
- stage management
- fuel consumption
- mass updates
- engine state
- separation logic

---

### Simulation Layer
Acts as mission control.

Responsibilities:
- manages all objects in the world
- applies physics each timestep
- handles mission events
- controls simulation states

---

### Rendering Layer
Handles visualization only.

Responsibilities:
- camera tracking
- drawing rocket and Earth
- particle effects
- trajectory visualization
- UI panels

Rendering never changes physics data.

---

## Physics Model

### Gravity

Newtonian gravitation:
F = G * M * m / r²

Where:
- G = gravitational constant
- M = Earth mass
- r = distance from Earth center

---

### Thrust
F_thrust = mass_flow_rate × exhaust_velocity

Rocket acceleration:
a = F_net / m
---

### Orbit Condition

A stable orbit occurs when:
centripetal force = gravitational force
Equivalent orbital velocity:
v = sqrt(GM / r)
---

## Supported Launch Vehicles

The simulator architecture supports configurable vehicles including:

- Falcon 9
- Falcon Heavy
- Atlas V
- Ariane 5 / Ariane 6
- Soyuz
- PSLV
- Electron
- Long March family
- Custom vehicles

Vehicle parameters are defined through mission profiles.

---

## Controls

| Key | Action |
|-----|--------|
| SPACE | Start Launch |
| RIGHT ARROW | Increase Time Warp |
| LEFT ARROW | Reduce Time Warp |
| ESC | Pause Simulation |

---

## Installation

### Requirements

- Python 3.10+
- pip
- virtual environment recommended

Install dependencies:

```bash
pip install pygame numpy
