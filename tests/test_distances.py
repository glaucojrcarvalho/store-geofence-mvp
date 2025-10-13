from types import SimpleNamespace
from app.services.distances import within_radius_and_distance


class DummyResult:
    def __init__(self, mapping):
        self._mapping = mapping

    def mappings(self):
        return self

    def first(self):
        return self._mapping


class DummyDB:
    def __init__(self, mapping):
        self._mapping = mapping

    def execute(self, sql, params):
        # ignore sql/params in this simple unit test
        return DummyResult(self._mapping)


def test_within_radius_and_distance_within():
    db = DummyDB({"within": True, "distance_m": 23.7})
    within, distance = within_radius_and_distance(db, store_id=1, lat=50.0, lng=30.0, radius_m=100)
    assert within is True
    assert abs(distance - 23.7) < 0.001


def test_within_radius_and_distance_no_location():
    db = DummyDB({"within": None, "distance_m": None})
    within, distance = within_radius_and_distance(db, store_id=1, lat=50.0, lng=30.0, radius_m=100)
    assert within is False
    assert distance is None


def test_within_radius_and_distance_no_row():
    class EmptyDB:
        def execute(self, sql, params):
            return SimpleNamespace(mappings=lambda: SimpleNamespace(first=lambda: None))

    db = EmptyDB()
    within, distance = within_radius_and_distance(db, store_id=1, lat=50.0, lng=30.0, radius_m=100)
    assert within is False
    assert distance is None

