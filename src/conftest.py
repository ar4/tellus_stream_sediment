import pytest

def pytest_addoption(parser):
    parser.addoption("--upstream", action="store")
    parser.addoption("--na", action="store")
    parser.addoption("--mg", action="store")
    parser.addoption("--al", action="store")

@pytest.fixture
def test_upstream(request):
    return request.config.getoption("--upstream")

@pytest.fixture
def test_na(request):
    return request.config.getoption("--na")

@pytest.fixture
def test_mg(request):
    return request.config.getoption("--mg")

@pytest.fixture
def test_al(request):
    return request.config.getoption("--al")
