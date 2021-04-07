from jasmine.utils import deep_get


def test_deep_get():
    d = {"A": {"B": {"C": 3}}}
    assert deep_get(d, "A", "B", "C") == 3
    assert deep_get(d, "A", "B", "C", "D") is None
    assert deep_get(d, "A", "B", "C", "D", default=89) == 89