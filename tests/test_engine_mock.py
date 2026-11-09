"""End-to-end smoke test using mock/offline Twitter data."""

from tweet_intelligence.engine import TweetIntelligenceEngine
from tweet_intelligence.storage.database import Storage


def test_analyze_demo_pipeline(tmp_path):
    db = tmp_path / "engine.db"
    storage = Storage(db_path=db)
    engine = TweetIntelligenceEngine(storage=storage, mock=True)
    ingested = engine.fetch_timeline(max_results=10)
    assert ingested > 0
    stats = engine.stats()
    assert stats["tweets"] == ingested
    assert stats["words"] > 0
    assert stats["structures"] > 0
    generated = engine.generate(count=2)
    assert len(generated) == 2
    assert engine.follow("learnerbot").startswith("[mock]")
