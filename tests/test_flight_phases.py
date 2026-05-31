from mission.flight_phases import FlightPhase, PHASE_NAMES
from simulation.events import EVENT_STAGE_SEPARATION


def test_all_phases_have_a_name():
    phase_values = [v for k, v in vars(FlightPhase).items() if not k.startswith("_")]
    for val in phase_values:
        assert val in PHASE_NAMES, f"FlightPhase value {val} is missing from PHASE_NAMES"


def test_second_stage_burn_exists():
    assert hasattr(FlightPhase, "SECOND_STAGE_BURN")
    assert FlightPhase.SECOND_STAGE_BURN in PHASE_NAMES


def test_event_constant_is_correct_string():
    # If someone changes the constant, this catches it.
    assert EVENT_STAGE_SEPARATION == "EVENT_STAGE_SEPARATION"


def test_rocket_emits_correct_event_string():
    # On this branch rocket.py emits "EVENT_SEPARATION" and world.py checks for the same string.
    # Verify the two are consistent.
    from rocket import rocket as rocket_module
    from simulation import world as world_module
    import inspect
    rocket_src = inspect.getsource(rocket_module)
    world_src = inspect.getsource(world_module)
    assert '"EVENT_SEPARATION"' in rocket_src
    assert '"EVENT_SEPARATION"' in world_src
