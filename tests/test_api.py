from fastapi.testclient import TestClient

from app.api import search as search_api
from app.db.session import get_session
from app.main import app
from app.rag.retriever import SearchResult

FAKE_RESULTS = [
    SearchResult(1, "code", "code/RewardExpirationService.java", "plusDays(365)", 0.91),
]

calls = []


def client(monkeypatch):
    calls.clear()

    def fake_search(session, q, k, mode):
        calls.append(mode)
        return FAKE_RESULTS

    monkeypatch.setattr(search_api.retriever, "search", fake_search)
    monkeypatch.setattr(search_api, "generate_answer", lambda q, r: "It adds 365 days. [1]")
    app.dependency_overrides[get_session] = lambda: None
    return TestClient(app)


def test_search(monkeypatch):
    resp = client(monkeypatch).get("/search", params={"q": "reward expiration"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["query"] == "reward expiration"
    assert body["mode"] == "hybrid"
    assert body["results"][0]["file"] == "code/RewardExpirationService.java"


def test_ask_returns_answer_and_numbered_sources(monkeypatch):
    resp = client(monkeypatch).post("/ask", json={"question": "Where is expiration calculated?"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["answer"].endswith("[1]")
    assert body["sources"] == [
        {"id": 1, "file": "code/RewardExpirationService.java", "score": 0.91}
    ]


def test_search_mode_is_passed_through(monkeypatch):
    resp = client(monkeypatch).get("/search", params={"q": "x", "mode": "keyword"})
    assert resp.status_code == 200
    assert calls == ["keyword"]


def test_unknown_search_mode_is_rejected(monkeypatch):
    resp = client(monkeypatch).get("/search", params={"q": "x", "mode": "magic"})
    assert resp.status_code == 422
