"""Sentence-structure analyze path used by the CLI."""

from tweet_intelligence.engine import TweetIntelligenceEngine
from tweet_intelligence.storage.database import Storage


def test_analyze_text_returns_structure_and_can_persist(tmp_path):
    db = tmp_path / "analyze.db"
    storage = Storage(db_path=db)
    engine = TweetIntelligenceEngine(storage=storage, mock=True)

    result = engine.analyze_text("I love simple projects.", persist=False)
    assert result["tokens"]
    assert result["structure"]
    assert storage.word_count() == 0

    result = engine.analyze_text("I love simple projects.", persist=True)
    assert storage.word_count() > 0
    assert storage.structure_count() == 1
    assert storage.get_structures()[0][0] == result["structure"]
