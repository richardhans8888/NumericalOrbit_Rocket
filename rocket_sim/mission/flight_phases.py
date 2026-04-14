# mission/flight_phases.py

class FlightPhase:
    PRELAUNCH = 0
    LIFTOFF = 1
    MAX_Q = 2
    GRAVITY_TURN = 3
    BOOSTER_BURNOUT = 4
    FAIRING_SEP = 5
    SECOND_STAGE_BURN = 6
    SECO = 7

PHASE_NAMES = {
    FlightPhase.PRELAUNCH: "PRELAUNCH",
    FlightPhase.LIFTOFF: "LIFTOFF",
    FlightPhase.MAX_Q: "MAX-Q",
    FlightPhase.GRAVITY_TURN: "GRAVITY TURN",
    FlightPhase.BOOSTER_BURNOUT: "BOOSTER BURNOUT",
    FlightPhase.FAIRING_SEP: "FAIRING SEPARATION",
    FlightPhase.SECOND_STAGE_BURN: "STAGE 2 BURN",
    FlightPhase.SECO: "SECO / ORBITAL COAST"
}
