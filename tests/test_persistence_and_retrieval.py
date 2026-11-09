"""Persistence across runs and efficient SQL retrieval used by generation."""

import random

from tweet_intelligence.generation.tweet_generator import TweetGenerator
from tweet_intelligence.storage.database import Storage


def test_persistence_across_runs(tmp_path):
    db = tmp_path / "persist.db"
    with Storage(db_path=db) as storage:
        storage.record_words([("python", "NNP"), ("idea", "NN")])
        storage.record_structure("NNP VBZ DT NN")
        storage.save_tweet("t1", "Python is a idea", author="bot", source="mock")

    # New connection / process simulation: reopen the same file.
    with Storage(db_path=db) as storage:
        assert storage.tweet_count() == 1
        assert ("python", "NNP", 1) in storage.get_all_words()
        assert ("NNP VBZ DT NN", 1) in storage.get_structures()


def test_efficient_indexes_exist(tmp_path):
    db = tmp_path / "idx.db"
    with Storage(db_path=db) as storage:
        names = storage.index_names()
    assert "idx_words_pos" in names
    assert "idx_words_count" in names
    assert "idx_structures_count" in names


def test_generation_uses_encountered_words_and_patterns(tmp_path):
    db = tmp_path / "learned.db"
    with Storage(db_path=db) as storage:
        storage.record_structure("NNP VBZ JJ")
        storage.record_words(
            [
                ("zebracode", "NNP"),
                ("feels", "VBZ"),
                ("luminescent", "JJ"),
            ]
        )
        generator = TweetGenerator(storage, rng=random.Random(42))
        tweets = generator.generate(count=5)

    vocabulary = {"zebracode", "feels", "luminescent"}
    for tweet in tweets:
        parts = {w.lower() for w in tweet.split()}
        assert parts <= vocabulary
        assert len(parts) == 3


def test_pos_prefix_retrieval(tmp_path):
    db = tmp_path / "prefix.db"
    with Storage(db_path=db) as storage:
        storage.record_words([("cat", "NN"), ("cats", "NNS"), ("run", "VB")])
        rows = storage.get_words_by_pos_prefix("NN", limit=10)
        words = {w for w, _ in rows}
        assert "cat" in words and "cats" in words
        assert "run" not in words
