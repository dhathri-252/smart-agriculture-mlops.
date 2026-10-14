"""Assistant endpoint tests — external AI calls are mocked (no key/network)."""

import io
import json
import os
import ssl
import sys
import urllib.error
from pathlib import Path
from unittest import mock

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.environ.setdefault("APP_DB_PATH", os.path.join(ROOT, "data", "test_app.db"))

from fastapi.testclient import TestClient  # noqa: E402

from api.main import app  # noqa: E402

OPENAI_KEY = "test-openai-key-123"  # placeholder, never a real credential

OPENAI_ENV = {
    "AI_PROVIDER": "openai",
    "OPENAI_API_KEY": OPENAI_KEY,
    "OPENAI_BASE_URL": "https://api.openai.com/v1",
}


def _ask(body: dict):
    return TestClient(app).post("/api/assistant", json=body)


class _FakeResponse:
    def __init__(self, payload):
        self._data = json.dumps(payload).encode("utf-8")

    def read(self):
        return self._data

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _openai_payload(text: str) -> dict:
    return {"choices": [{"message": {"content": text}}]}


def test_knowledge_base_answers_english_and_telugu():
    r = _ask({"question": "How to manage soil pH?", "language": "en"})
    assert r.status_code == 200
    body = r.json()
    assert body["provider"] == "knowledge_base"
    assert "en" in body["answer"] and "te" in body["answer"]
    assert "pH" in body["answer"]["en"]

    r = _ask({"question": "How often should I irrigate rice?", "language": "te"})
    assert r.status_code == 200
    assert r.json()["provider"] == "knowledge_base"
    assert r.json()["answer"]["te"]  # Telugu answer present


def test_unknown_question_returns_honest_fallback():
    r = _ask({"question": "zzz qqq wobble", "language": "en"})
    body = r.json()
    assert body["provider"] == "knowledge_base"
    assert "don't have a specific answer" in body["answer"]["en"]


def test_validation_errors():
    assert _ask({"question": ""}).status_code == 422
    assert _ask({}).status_code == 422
    assert _ask({"question": "x" * 1001}).status_code == 422


def test_repeated_questions_are_stateless_and_work():
    first = _ask({"question": "What about soil pH?", "language": "en"})
    second = _ask({"question": "What about soil pH?", "language": "en"})
    assert first.status_code == second.status_code == 200
    assert first.json()["answer"] == second.json()["answer"]


def test_openai_provider_used_when_configured():
    with mock.patch.dict(os.environ, OPENAI_ENV):
        with mock.patch(
            "api.services.assistant.urllib.request.urlopen",
            return_value=_FakeResponse(_openai_payload("Water in the early morning.")),
        ) as fake:
            r = _ask({"question": "When should I irrigate?", "language": "en"})
    assert r.status_code == 200
    body = r.json()
    assert body["provider"] == "openai"
    assert body["answer"]["en"] == "Water in the early morning."
    # Key stays server-side: sent to the provider, never in the response.
    request = fake.call_args[0][0]
    assert request.get_header("Authorization") == f"Bearer {OPENAI_KEY}"
    assert OPENAI_KEY not in r.text
    # TLS context is passed (this Python build has no system CA bundle).
    assert isinstance(fake.call_args[1]["context"], ssl.SSLContext)


def test_openai_failure_falls_back_to_knowledge_base():
    with mock.patch.dict(os.environ, OPENAI_ENV):
        with mock.patch(
            "api.services.assistant.urllib.request.urlopen",
            side_effect=urllib.error.URLError("boom"),
        ):
            r = _ask({"question": "How to manage soil pH?", "language": "en"})
    assert r.status_code == 200
    assert r.json()["provider"] == "knowledge_base"
    assert OPENAI_KEY not in r.text


def test_weather_context_is_added_to_ai_prompt_only_when_provided():
    weather = {
        "location": "London, England, GB",
        "temperature": 18.5,
        "humidity": 87,
        "condition": "Clouds",
    }
    with mock.patch.dict(os.environ, OPENAI_ENV):
        with mock.patch(
            "api.services.assistant.urllib.request.urlopen",
            return_value=_FakeResponse(_openai_payload("Given the cloudy weather...")),
        ) as fake:
            r = _ask({"question": "Should I irrigate today?", "language": "en",
                      "weather": weather})
        prompt_with = json.loads(fake.call_args[0][0].data)["messages"][0]["content"]
        assert "London, England, GB" in prompt_with
        assert "18.5°C" in prompt_with
        assert "not a forecast" in prompt_with  # observations clearly ≠ forecast
        assert "Current weather observations" in prompt_with

        with mock.patch(
            "api.services.assistant.urllib.request.urlopen",
            return_value=_FakeResponse(_openai_payload("Sure.")),
        ) as fake2:
            _ask({"question": "Should I irrigate today?", "language": "en"})
        prompt_without = json.loads(fake2.call_args[0][0].data)["messages"][0]["content"]
        assert "London" not in prompt_without


def test_knowledge_base_tolerates_weather_context():
    r = _ask({
        "question": "Tell me about irrigation",
        "language": "en",
        "weather": {"location": "Sydney, AU", "temperature": 17.2, "condition": "Rain"},
    })
    assert r.status_code == 200
    body = r.json()
    assert body["provider"] == "knowledge_base"
    assert "irrigation" in body["answer"]["en"].lower()


def _http_error(code: int, body: dict) -> urllib.error.HTTPError:
    return urllib.error.HTTPError(
        "https://api.openai.com/v1/chat/completions",
        code, "error", {}, io.BytesIO(json.dumps(body).encode("utf-8")),
    )


def test_openai_telugu_response_keyed_by_language():
    telugu_text = "నేల ఆరోగ్యానికి కంపోస్ట్ వేసి, పంట మార్పిడి పాటించండి."
    with mock.patch.dict(os.environ, OPENAI_ENV):
        with mock.patch(
            "api.services.assistant.urllib.request.urlopen",
            return_value=_FakeResponse(_openai_payload(telugu_text)),
        ):
            r = _ask({"question": "నేల ఆరోగ్యం ఎలా మెరుగుపరచాలి?", "language": "te"})
    assert r.status_code == 200
    body = r.json()
    assert body["provider"] == "openai"
    assert body["language"] == "te"
    assert body["answer"]["te"] == telugu_text


def test_system_prompt_requires_telugu_script_for_telugu_requests():
    with mock.patch.dict(os.environ, OPENAI_ENV):
        with mock.patch(
            "api.services.assistant.urllib.request.urlopen",
            return_value=_FakeResponse(_openai_payload("Okay.")),
        ) as fake:
            _ask({"question": "విత్తనాల ఎంపిక ఎలా?", "language": "te"})
    prompt = json.loads(fake.call_args[0][0].data)["messages"][0]["content"]
    assert "Telugu script" in prompt
    assert "sustainable farming" in prompt  # farming domains covered


def test_missing_configuration_uses_knowledge_base_without_any_http_call():
    with mock.patch.dict(os.environ, {"AI_PROVIDER": "openai", "OPENAI_API_KEY": ""}):
        with mock.patch(
            "api.services.assistant.urllib.request.urlopen"
        ) as fake:
            r = _ask({"question": "How to manage soil pH?", "language": "en"})
    assert r.status_code == 200
    assert r.json()["provider"] == "knowledge_base"
    fake.assert_not_called()


def test_timeout_falls_back_to_knowledge_base():
    with mock.patch.dict(os.environ, OPENAI_ENV):
        with mock.patch(
            "api.services.assistant.urllib.request.urlopen",
            side_effect=TimeoutError("timed out"),
        ):
            r = _ask({"question": "When should I harvest rice?", "language": "en"})
    assert r.status_code == 200
    body = r.json()
    assert body["provider"] == "knowledge_base"
    assert body["answer"]["en"]  # a real KB answer, not an error


def test_provider_http_errors_fall_back_without_leaking_key():
    for code, err_body in (
        (401, {"error": {"message": "Incorrect API key provided"}}),
        (429, {"error": {"message": "rate limit exceeded"}}),
    ):
        with mock.patch.dict(os.environ, OPENAI_ENV):
            with mock.patch(
                "api.services.assistant.urllib.request.urlopen",
                side_effect=_http_error(code, err_body),
            ):
                r = _ask({"question": "How to manage soil pH?", "language": "en"})
        assert r.status_code == 200
        assert r.json()["provider"] == "knowledge_base"
        assert OPENAI_KEY not in r.text  # key never leaks, whatever the failure


def test_openai_timeout_is_configurable_and_clamped():
    from api.config import get_openai_timeout_seconds

    with mock.patch.dict(os.environ, {"OPENAI_TIMEOUT_SECONDS": "7"}):
        assert get_openai_timeout_seconds() == 7
    with mock.patch.dict(os.environ, {"OPENAI_TIMEOUT_SECONDS": "999"}):
        assert get_openai_timeout_seconds() == 60
    with mock.patch.dict(os.environ, {"OPENAI_TIMEOUT_SECONDS": "1"}):
        assert get_openai_timeout_seconds() == 5
    with mock.patch.dict(os.environ, {"OPENAI_TIMEOUT_SECONDS": "abc"}):
        assert get_openai_timeout_seconds() == 20
    with mock.patch.dict(os.environ, {"OPENAI_TIMEOUT_SECONDS": ""}):
        assert get_openai_timeout_seconds() == 20


def test_request_uses_configured_timeout_and_tls_context():
    env = {**OPENAI_ENV, "OPENAI_TIMEOUT_SECONDS": "7"}
    with mock.patch.dict(os.environ, env):
        with mock.patch(
            "api.services.assistant.urllib.request.urlopen",
            return_value=_FakeResponse(_openai_payload("Answer.")),
        ) as fake:
            _ask({"question": "What is compost?", "language": "en"})
    assert fake.call_args[1]["timeout"] == 7
    assert isinstance(fake.call_args[1]["context"], ssl.SSLContext)


# --- Knowledge-base matching regressions (reported fallback issue) ----------

FALLBACK_EN = "I don't have a specific answer for that yet"
FALLBACK_TE = "దీనికి ప్రత్యేకమైన సమాధానం ఇంకా లేదు"


@pytest.mark.parametrize(
    "question,marker",
    [
        # Natural variations that previously fell through to the fallback.
        ("What crop should I plant this season?", "Crop Prediction form"),
        ("How much water does wheat need?", "Irrigation tips"),
        ("When is the right time to sow wheat?", "Sowing basics"),
        ("When to grow tomatoes?", "Sowing basics"),          # phrase beats "grow"
        ("How do I control pests on my vegetables?", "Pest & disease"),
        ("How can I increase the yield?", "Harvest tips"),
        ("Will it rain tomorrow?", "Weather & farming"),
        ("Where can I sell my produce at a good price?", "Market & schemes"),
        ("Which fertilizer is better for tomatoes?", "Fertiliser basics"),
        ("post-harvest storage tips", "Harvest tips"),        # hyphen normalisation
        ("Hi, what do you know about farming?", "Hello!"),    # punctuation after "hi"
        ("Can I transplant the seedlings now?", "Sowing basics"),
        ("How do I start composting on my farm?", "Soil health"),
    ],
)
def test_kb_matches_natural_question_variations(question, marker):
    r = _ask({"question": question, "language": "en"})
    assert r.status_code == 200
    body = r.json()
    assert body["provider"] == "knowledge_base"
    assert FALLBACK_EN not in body["answer"]["en"], question
    assert marker in body["answer"]["en"], question


@pytest.mark.parametrize(
    "question,marker",
    [
        # Telugu questions with grammatical suffixes must match topic stems.
        ("పురుగులను ఎలా నియంత్రించాలి?", "తెగుళ్లు"),          # pests
        ("నేల సారం ఎలా పెంచాలి?", "నేల ఆరోగ్యం"),                # soil
        ("విత్తనాలు ఎలా ఎంచుకోవాలి?", "విత్తనాలు"),             # sowing
        ("వర్షాకాలంలో ఏం చేయాలి?", "వాతావరణం"),                 # weather
        ("ఎరువులు ఎప్పుడు వేయాలి?", "ఎరువులు"),                  # fertiliser
        ("మంచి ధర ఉన్న మార్కెట్ ఎక్కడ?", "మార్కెట్"),              # market
        ("పంట ఎప్పుడు కోయాలి?", "కోత"),                          # harvest
    ],
)
def test_kb_matches_telugu_questions(question, marker):
    r = _ask({"question": question, "language": "te"})
    assert r.status_code == 200
    body = r.json()
    assert body["provider"] == "knowledge_base"
    assert FALLBACK_TE not in body["answer"]["te"], question
    assert marker in body["answer"]["te"], question


@pytest.mark.parametrize(
    "question",
    [
        "What is the capital of France?",   # not farming-related
        "photosynthesis",                   # unrelated biology term
        "zzz qqq wobble",                   # nonsense
    ],
)
def test_genuinely_unsupported_questions_keep_helpful_fallback(question):
    r = _ask({"question": question, "language": "en"})
    assert r.status_code == 200
    body = r.json()
    assert body["provider"] == "knowledge_base"
    assert FALLBACK_EN in body["answer"]["en"]


def test_no_unrelated_topic_is_returned_to_avoid_fallback():
    # "pepper" must not false-match the pest topic; it routes to crop guidance
    # via "grow" rather than an unrelated pest answer.
    r = _ask({"question": "How do I grow black pepper?", "language": "en"})
    body = r.json()
    assert "Pest & disease" not in body["answer"]["en"]
    assert (
        FALLBACK_EN in body["answer"]["en"] or "Crop Prediction" in body["answer"]["en"]
    )
