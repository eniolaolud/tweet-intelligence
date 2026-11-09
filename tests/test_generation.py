"""Tests for tweet generation from stored words and patterns."""

import random

from tweet_intelligence.generation.tweet_generator import TweetGenerator
from tweet_intelligence.storage.database import Storage


def test_generate_uses_stored_patterns_and_words(tmp_path):
    db = tmp_path / "gen.db"
    with Storage(db_path=db) as storage:
        storage.record_structure("PRP VBP JJ NN")
        storage.record_words(
            [
                ("i", "PRP"),
                ("love", "VBP"),
                ("simple", "JJ"),
                ("projects", "NN"),
            ]
        )
        generator = TweetGenerator(storage, rng=random.Random(0))
        tweets = generator.generate(count=3)
        assert len(tweets) == 3
        for tweet in tweets:
            assert tweet
            assert tweet[0].isupper()
            # Four POS slots → four words.
            assert len(tweet.split()) == 4


def test_generate_works_with_empty_storage(tmp_path):
    db = tmp_path / "empty.db"
    with Storage(db_path=db) as storage:
        generator = TweetGenerator(storage, rng=random.Random(1))
        tweets = generator.generate(count=2)
        assert len(tweets) == 2
        assert all(t.strip() for t in tweets)
