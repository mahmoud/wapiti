import pytest


def pytest_addoption(parser):
    parser.addoption("--mag", action="store", type="int", default=1,
                     help="magnitude of the operation limits")


@pytest.fixture
def mag(request):
    return request.config.getoption("--mag")
