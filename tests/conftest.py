import json
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"
PROJECT_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def fixture_json():
    def _load(name: str):
        return json.loads((FIXTURES / name).read_text(encoding="utf-8"))
    return _load


@pytest.fixture
def fixture_text():
    def _load(name: str):
        return (FIXTURES / name).read_text(encoding="utf-8")
    return _load


@pytest.fixture
def skills_dictionary() -> Path:
    return PROJECT_ROOT / "config" / "skills_dictionary.yaml"


class FakeResponse:
    def __init__(self, status_code=200, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload
        self.text = text

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class FakeClient:
    """Remplace HttpClient : renvoie des réponses préparées, enregistre les appels."""

    def __init__(self, responses, allowed=True):
        self.responses = list(responses)
        self.calls = []
        self.allowed = allowed

    def get(self, url, **kwargs):
        self.calls.append(("GET", url, kwargs))
        return self.responses.pop(0)

    def post(self, url, **kwargs):
        self.calls.append(("POST", url, kwargs))
        return self.responses.pop(0)

    def allowed_by_robots(self, url):
        return self.allowed


@pytest.fixture
def fake_response():
    return FakeResponse


@pytest.fixture
def fake_client():
    return FakeClient
