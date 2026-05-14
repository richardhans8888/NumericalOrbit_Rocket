from rocket.fuel_system import FuelSystem


def test_normal_consumption():
    fs = FuelSystem(100.0)
    consumed = fs.consume(30.0)
    assert consumed == 30.0
    assert fs.fuel == 70.0
    assert not fs.empty


def test_cannot_consume_more_than_available():
    fs = FuelSystem(50.0)
    consumed = fs.consume(200.0)
    assert consumed == 50.0
    assert fs.fuel == 0.0
    assert fs.empty


def test_empty_flag_triggers_at_zero():
    fs = FuelSystem(10.0)
    fs.consume(10.0)
    assert fs.empty


def test_consume_returns_zero_when_already_empty():
    fs = FuelSystem(0.0)
    assert fs.empty
    assert fs.consume(50.0) == 0.0


def test_total_consumed_tracks_correctly():
    fs = FuelSystem(100.0)
    fs.consume(40.0)
    fs.consume(30.0)
    assert fs.consumed == 70.0
