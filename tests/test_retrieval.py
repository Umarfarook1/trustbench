from trustbench.retrieval.index import Doc, KnowledgeIndex


def test_search_ranks_lexically_closest_doc_first(fake_embedder):
    docs = [
        Doc(id="refunds", title="Refunds", text="refund refunds transaction"),
        Doc(id="kyc", title="KYC", text="kyc identity verification"),
        Doc(id="cards", title="Cards", text="card freeze frozen"),
    ]
    index = KnowledgeIndex(fake_embedder)
    index.build(docs)

    hits = index.search("how do refunds work for a transaction", k=2)

    assert hits[0][0].id == "refunds"
    assert len(hits) == 2
    assert hits[0][1] >= hits[1][1]  # scores are descending


def test_search_handles_zero_overlap_without_crashing(fake_embedder):
    docs = [Doc(id="cards", title="Cards", text="card freeze frozen")]
    index = KnowledgeIndex(fake_embedder)
    index.build(docs)

    hits = index.search("subscription billing question", k=1)

    assert len(hits) == 1
    assert hits[0][1] == 0.0  # no shared vocabulary, cosine is zero, no NaN
