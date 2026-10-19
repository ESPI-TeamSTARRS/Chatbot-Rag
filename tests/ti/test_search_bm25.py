from chatbot_rag.adapters.output.search_bm25 import Bm25DocSearch


def make_corpus(tmp_path):
    (tmp_path / "errors-cases").mkdir()
    (tmp_path / "actions-taken").mkdir()
    (tmp_path / "errors-cases" / "redis.md").write_text(
        "# Redis timeout\n\nConnection timed out.\n\n## Procedure\n\nRestart the redis sentinel.\n"
    )
    (tmp_path / "errors-cases" / "disk.md").write_text(
        "# Disk full\n\n## Procedure\n\nPurge old logs under /var/log.\n"
    )
    (tmp_path / "actions-taken" / "old-20260101-000000.md").write_text(
        "# Report\n\nzebracorn quirk\n"
    )
    return tmp_path


def test_relevant_document_ranked_first(tmp_path):
    search = Bm25DocSearch(make_corpus(tmp_path))
    hits = search.search("redis sentinel restart", limit=3)
    assert hits[0].path == "errors-cases/redis.md"


def test_no_match_returns_empty(tmp_path):
    search = Bm25DocSearch(make_corpus(tmp_path))
    assert search.search("kubernetes", limit=3) == []


def test_actions_taken_excluded(tmp_path):
    search = Bm25DocSearch(make_corpus(tmp_path))
    assert search.search("zebracorn", limit=3) == []


def test_hit_is_the_whole_document(tmp_path):
    hit = Bm25DocSearch(make_corpus(tmp_path)).search("purge logs", limit=1)[0]
    assert hit.path == "errors-cases/disk.md"
    assert hit.text == "# Disk full\n\n## Procedure\n\nPurge old logs under /var/log."


def test_one_call_returns_the_best_documents_up_to_the_limit(tmp_path):
    corpus = make_corpus(tmp_path)
    for i in range(6):
        (corpus / "errors-cases" / f"extra{i}.md").write_text(f"# Extra {i}\n\nredis problem {i}\n")
    paths = [hit.path for hit in Bm25DocSearch(corpus).search("redis", limit=5)]
    assert len(paths) == 5 and paths[0] == "errors-cases/redis.md"


def test_empty_corpus(tmp_path):
    assert Bm25DocSearch(tmp_path).search("anything", limit=3) == []


def test_edited_document_is_searchable_without_restart(tmp_path):
    corpus = make_corpus(tmp_path)
    search = Bm25DocSearch(corpus)
    assert search.search("kubernetes", limit=3) == []
    (corpus / "errors-cases" / "disk.md").write_text("# Disk full\n\nKubernetes evicts pods.\n")
    assert search.search("kubernetes", limit=3)[0].path == "errors-cases/disk.md"


def test_new_and_removed_documents_are_picked_up_without_restart(tmp_path):
    corpus = make_corpus(tmp_path)
    search = Bm25DocSearch(corpus)
    (corpus / "errors-cases" / "net.md").write_text("# Network\n\nDNS resolution fails.\n")
    assert search.search("dns", limit=3)[0].path == "errors-cases/net.md"
    (corpus / "errors-cases" / "net.md").unlink()
    assert search.search("dns", limit=3) == []
