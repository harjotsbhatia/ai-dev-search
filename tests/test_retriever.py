from app.rag.retriever import SearchResult, build_tsquery, reciprocal_rank_fusion


def result(id_: int) -> SearchResult:
    return SearchResult(id_, "docs", f"file{id_}.md", "", 0.0)


def test_build_tsquery_ors_words_and_splits_camel_case():
    assert build_tsquery("Where is RewardExpirationService?") == (
        "Where | is | Reward | Expiration | Service"
    )


def test_build_tsquery_strips_operators():
    assert build_tsquery("a & b | !c") == "a | b | c"
    assert build_tsquery("?!") == ""


def test_rrf_rewards_results_found_by_both_lists():
    vector = [result(1), result(2), result(3)]
    keyword = [result(3), result(4)]
    fused = reciprocal_rank_fusion([vector, keyword], top_k=4)
    # 3 is 3rd in one list and 1st in the other, which beats 1st in only one list.
    # 2 and 4 are each 2nd in one list, so they tie and keep first-seen order.
    assert [r.id for r in fused] == [3, 1, 2, 4]
    assert fused[0].score == round(1 / 63 + 1 / 61, 4)


def test_rrf_respects_top_k():
    fused = reciprocal_rank_fusion([[result(1), result(2), result(3)]], top_k=2)
    assert [r.id for r in fused] == [1, 2]
