"""High-level orchestration: fetch → analyze → store → generate."""

from __future__ import annotations

from tweet_intelligence.analysis.nltk_analyzer import Analyzer
from tweet_intelligence.api.twitter_client import TwitterClient, Tweet, create_client
from tweet_intelligence.generation.tweet_generator import TweetGenerator
from tweet_intelligence.storage.database import Storage


class TweetIntelligenceEngine:
    """Glue the modules together for CLI commands and scripts."""

    def __init__(
        self,
        storage: Storage | None = None,
        client: TwitterClient | None = None,
        *,
        mock: bool | None = None,
    ) -> None:
        self.storage = storage or Storage()
        self.client = client or create_client(mock=mock)
        self.analyzer = Analyzer()
        self.generator = TweetGenerator(self.storage)

    def ingest_tweets(self, tweets: list[Tweet], source: str = "live") -> int:
        """Analyze and persist a list of tweets. Returns how many were ingested."""
        ingested = 0
        for tweet in tweets:
            self.storage.save_tweet(
                tweet_id=tweet.id,
                text=tweet.text,
                author=tweet.author,
                source=source,
            )
            result = self.analyzer.analyze(tweet.text)
            if result.tokens:
                self.storage.record_words(result.tokens)
            if result.structure:
                self.storage.record_structure(result.structure)
            ingested += 1
        return ingested

    def fetch_timeline(self, max_results: int = 20) -> int:
        tweets = self.client.get_home_timeline(max_results=max_results)
        source = "mock" if self.client.__class__.__name__.startswith("Mock") else "live"
        return self.ingest_tweets(tweets, source=source)

    def fetch_user(self, username: str, max_results: int = 20) -> int:
        tweets = self.client.get_user_timeline(username, max_results=max_results)
        source = "mock" if self.client.__class__.__name__.startswith("Mock") else "live"
        return self.ingest_tweets(tweets, source=source)

    def follow(self, username: str) -> str:
        return self.client.follow_user(username)

    def analyze_text(self, text: str, *, persist: bool = False) -> dict[str, object]:
        """Analyze sentence structure with NLTK; optionally store words/patterns."""
        result = self.analyzer.analyze(text)
        if persist and result.tokens:
            self.storage.record_words(result.tokens)
            if result.structure:
                self.storage.record_structure(result.structure)
        return {
            "tokens": result.tokens,
            "structure": result.structure,
        }

    def generate(self, count: int = 1) -> list[str]:
        return self.generator.generate(count=count)

    def stats(self) -> dict[str, int]:
        return {
            "tweets": self.storage.tweet_count(),
            "words": self.storage.word_count(),
            "structures": self.storage.structure_count(),
        }
