import pytest

def pytest_addoption(parser):
    parser.addoption("--upstream", action="store")
    parser.addoption("--na", action="store")
    parser.addoption("--mg", action="store")
    parser.addoption("--al", action="store")
    parser.addoption("--si", action="store")
    parser.addoption("--p2", action="store")
    parser.addoption("--s_", action="store")

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

@pytest.fixture
def test_si(request):
    return request.config.getoption("--si")

@pytest.fixture
def test_p2(request):
    return request.config.getoption("--p2")

@pytest.fixture
def test_s(request):
    return request.config.getoption("--s_")
