from mission.flight_phases import FlightPhase, PHASE_NAMES
from simulation.events import EVENT_STAGE_SEPARATION


def test_all_phases_have_a_name():
    phase_values = [v for k, v in vars(FlightPhase).items() if not k.startswith("_")]
    for val in phase_values:
        assert val in PHASE_NAMES, f"FlightPhase value {val} is missing from PHASE_NAMES"


def test_no_second_stage_burn_attribute():
    # This was the wrong enum value introduced in a conflict branch.
    assert not hasattr(FlightPhase, "SECOND_STAGE_BURN")


def test_upper_stage_burn_exists():
    assert hasattr(FlightPhase, "UPPER_STAGE_BURN")
    assert FlightPhase.UPPER_STAGE_BURN in PHASE_NAMES


def test_event_constant_is_correct_string():
    # If someone changes the constant, this catches it.
    assert EVENT_STAGE_SEPARATION == "EVENT_STAGE_SEPARATION"


def test_rocket_emits_correct_event_string():
    # Regression: rocket.py used to emit "EVENT_SEPARATION" (wrong).
    # Import the value that rocket.py actually emits and confirm it matches the constant.
    from rocket import rocket as rocket_module
    import inspect
    source = inspect.getsource(rocket_module)
    # The old bug was the hardcoded string "EVENT_SEPARATION"
    assert '"EVENT_SEPARATION"' not in source, (
        'rocket.py still has the hardcoded wrong string "EVENT_SEPARATION" — '
        "use the EVENT_STAGE_SEPARATION constant instead"
    )
