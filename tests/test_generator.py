from app.rag.generator import build_messages
from app.rag.retriever import SearchResult


def test_context_numbers_sources_in_order():
    results = [
        SearchResult(1, "code", "code/RewardExpirationService.java", "plusDays(365)", 0.9),
        SearchResult(2, "docs", "docs/rewards-architecture.md", "expire 365 days", 0.8),
    ]
    messages = build_messages("Where is expiration calculated?", results)
    user = messages[1]["content"]
    assert "[1] code/RewardExpirationService.java" in user
    assert "[2] docs/rewards-architecture.md" in user
    assert user.index("[1]") < user.index("[2]")
    assert "only the provided context" in messages[0]["content"]
