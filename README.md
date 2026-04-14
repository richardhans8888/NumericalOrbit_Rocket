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

## Project Architecture
