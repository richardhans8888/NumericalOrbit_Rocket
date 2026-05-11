# mission/flight_phases.py

class FlightPhase:
    PRELAUNCH = 0
    LIFTOFF = 1
    MAX_Q = 2
    GRAVITY_TURN = 3
    BOOSTER_BURNOUT = 4
    FAIRING_SEP = 5
    UPPER_STAGE_BURN = 6
    SECO = 7

PHASE_NAMES = {
    FlightPhase.PRELAUNCH: "PRELAUNCH",
    FlightPhase.LIFTOFF: "LIFTOFF",
    FlightPhase.MAX_Q: "MAX-Q",
    FlightPhase.GRAVITY_TURN: "GRAVITY TURN",
    FlightPhase.BOOSTER_BURNOUT: "BOOSTER BURNOUT",
    FlightPhase.FAIRING_SEP: "FAIRING SEPARATION",
    FlightPhase.UPPER_STAGE_BURN: "UPPER STAGE BURN",
    FlightPhase.SECO: "SECO / ORBITAL COAST"
}
