import pytest


@pytest.fixture
def clean_bucket():
    yield {}
