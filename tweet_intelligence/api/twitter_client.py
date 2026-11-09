"""Twitter API integration with an offline mock fallback."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from dotenv import load_dotenv

# Sample tweets ship with the package for offline/demo mode.
SAMPLE_DATA_PATH = Path(__file__).resolve().parent.parent / "sample_data" / "sample_tweets.json"


@dataclass(frozen=True)
class Tweet:
    """A normalized tweet used across the app."""

    id: str
    text: str
    author: str


class TwitterClient(Protocol):
    """Shared interface for live and mock Twitter clients."""

    def get_home_timeline(self, max_results: int = 20) -> list[Tweet]:
        ...

    def get_user_timeline(self, username: str, max_results: int = 20) -> list[Tweet]:
        ...

    def follow_user(self, username: str) -> str:
        ...


def credentials_available() -> bool:
    """Return True when enough env vars exist for a live Twitter client."""
    load_dotenv()
    bearer = os.getenv("TWITTER_BEARER_TOKEN", "").strip()
    api_key = os.getenv("TWITTER_API_KEY", "").strip()
    api_secret = os.getenv("TWITTER_API_SECRET", "").strip()
    access_token = os.getenv("TWITTER_ACCESS_TOKEN", "").strip()
    access_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET", "").strip()
    # Bearer token alone can read public timelines; user context needed to follow.
    return bool(bearer) or all([api_key, api_secret, access_token, access_secret])


def create_client(*, mock: bool | None = None) -> TwitterClient:
    """
    Build a Twitter client.

    - mock=True  → always use sample data
    - mock=False → require live credentials
    - mock=None  → use live credentials when present, otherwise mock
    """
    load_dotenv()
    if mock is True:
        return MockTwitterClient()
    if mock is False:
        return LiveTwitterClient()
    if credentials_available():
        return LiveTwitterClient()
    return MockTwitterClient()


class MockTwitterClient:
    """Offline client that returns bundled sample tweets."""

    def __init__(self, sample_path: Path | None = None) -> None:
        path = sample_path or SAMPLE_DATA_PATH
        with path.open(encoding="utf-8") as handle:
            raw = json.load(handle)
        self._tweets = [
            Tweet(id=item["id"], text=item["text"], author=item["author"])
            for item in raw
        ]
        self._followed: list[str] = []

    def get_home_timeline(self, max_results: int = 20) -> list[Tweet]:
        return self._tweets[:max_results]

    def get_user_timeline(self, username: str, max_results: int = 20) -> list[Tweet]:
        username = username.lstrip("@").lower()
        matches = [t for t in self._tweets if t.author.lower() == username]
        if matches:
            return matches[:max_results]
        # Fall back to all sample tweets so demo mode always has data.
        return self._tweets[:max_results]

    def follow_user(self, username: str) -> str:
        username = username.lstrip("@")
        self._followed.append(username)
        return f"[mock] Now following @{username}"


class LiveTwitterClient:
    """
    Live Twitter API v2 client via tweepy.

    Required env vars (see .env.example):
      TWITTER_BEARER_TOKEN — read timelines
      TWITTER_API_KEY / TWITTER_API_SECRET / TWITTER_ACCESS_TOKEN /
      TWITTER_ACCESS_TOKEN_SECRET — follow users (user context)
    """

    def __init__(self) -> None:
        import tweepy

        load_dotenv()
        bearer = os.getenv("TWITTER_BEARER_TOKEN", "").strip() or None
        api_key = os.getenv("TWITTER_API_KEY", "").strip() or None
        api_secret = os.getenv("TWITTER_API_SECRET", "").strip() or None
        access_token = os.getenv("TWITTER_ACCESS_TOKEN", "").strip() or None
        access_secret = os.getenv("TWITTER_ACCESS_TOKEN_SECRET", "").strip() or None

        if not bearer and not all([api_key, api_secret, access_token, access_secret]):
            raise RuntimeError(
                "Twitter credentials missing. Set TWITTER_BEARER_TOKEN and/or "
                "OAuth 1.0a keys in your environment (see .env.example), "
                "or pass --mock for offline mode."
            )

        self._client = tweepy.Client(
            bearer_token=bearer,
            consumer_key=api_key,
            consumer_secret=api_secret,
            access_token=access_token,
            access_token_secret=access_secret,
            wait_on_rate_limit=True,
        )
        self._has_user_context = all(
            [api_key, api_secret, access_token, access_secret]
        )

    def get_home_timeline(self, max_results: int = 20) -> list[Tweet]:
        if not self._has_user_context:
            raise RuntimeError(
                "Home timeline requires OAuth user context "
                "(TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, "
                "TWITTER_ACCESS_TOKEN_SECRET)."
            )
        max_results = max(5, min(max_results, 100))
        response = self._client.get_home_timeline(
            max_results=max_results,
            tweet_fields=["author_id"],
            expansions=["author_id"],
            user_fields=["username"],
            user_auth=True,
        )
        return self._normalize(response)

    def get_user_timeline(self, username: str, max_results: int = 20) -> list[Tweet]:
        username = username.lstrip("@")
        user = self._client.get_user(username=username)
        if not user or not user.data:
            raise RuntimeError(f"User @{username} not found.")
        max_results = max(5, min(max_results, 100))
        response = self._client.get_users_tweets(
            id=user.data.id,
            max_results=max_results,
            tweet_fields=["author_id"],
            exclude=["retweets", "replies"],
        )
        tweets: list[Tweet] = []
        if response and response.data:
            for item in response.data:
                tweets.append(
                    Tweet(id=str(item.id), text=item.text, author=username)
                )
        return tweets

    def follow_user(self, username: str) -> str:
        if not self._has_user_context:
            raise RuntimeError(
                "Following users requires OAuth user context "
                "(TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, "
                "TWITTER_ACCESS_TOKEN_SECRET)."
            )
        username = username.lstrip("@")
        # Confirm the authenticated user context is valid before following.
        me = self._client.get_me(user_auth=True)
        if not me or not me.data:
            raise RuntimeError("Could not resolve authenticated user (get_me).")
        target = self._client.get_user(username=username, user_auth=True)
        if not target or not target.data:
            raise RuntimeError(f"User @{username} not found.")
        # tweepy Client.follow_user takes target_user_id only (auth user is implied).
        self._client.follow_user(target_user_id=target.data.id, user_auth=True)
        return f"Now following @{username}"

    @staticmethod
    def _normalize(response: object) -> list[Tweet]:
        tweets: list[Tweet] = []
        if not response or not getattr(response, "data", None):
            return tweets
        users_by_id: dict[str, str] = {}
        includes = getattr(response, "includes", None) or {}
        for user in includes.get("users", []) or []:
            users_by_id[str(user.id)] = user.username
        for item in response.data:
            author_id = str(getattr(item, "author_id", "") or "")
            author = users_by_id.get(author_id, author_id or "unknown")
            tweets.append(Tweet(id=str(item.id), text=item.text, author=author))
        return tweets
