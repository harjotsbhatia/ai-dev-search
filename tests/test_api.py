from fastapi.testclient import TestClient

from app.api import search as search_api
from app.db.session import get_session
from app.main import app
from app.rag.retriever import SearchResult

FAKE_RESULTS = [
    SearchResult(1, "code", "code/RewardExpirationService.java", "plusDays(365)", 0.91),
]


def client(monkeypatch):
    monkeypatch.setattr(search_api.retriever, "search", lambda session, q, k: FAKE_RESULTS)
    monkeypatch.setattr(search_api, "generate_answer", lambda q, r: "It adds 365 days. [1]")
    app.dependency_overrides[get_session] = lambda: None
    return TestClient(app)


def test_search(monkeypatch):
    resp = client(monkeypatch).get("/search", params={"q": "reward expiration"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["query"] == "reward expiration"
    assert body["results"][0]["file"] == "code/RewardExpirationService.java"


def test_ask_returns_answer_and_numbered_sources(monkeypatch):
    resp = client(monkeypatch).post("/ask", json={"question": "Where is expiration calculated?"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["answer"].endswith("[1]")
    assert body["sources"] == [
        {"id": 1, "file": "code/RewardExpirationService.java", "score": 0.91}
    ]
