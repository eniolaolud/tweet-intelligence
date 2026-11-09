"""Prove LiveTwitterClient calls the real Twitter API (tweepy), without network."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from tweet_intelligence.api.twitter_client import LiveTwitterClient, Tweet


def _env(monkeypatch):
    monkeypatch.setenv("TWITTER_BEARER_TOKEN", "bearer-test")
    monkeypatch.setenv("TWITTER_API_KEY", "key")
    monkeypatch.setenv("TWITTER_API_SECRET", "secret")
    monkeypatch.setenv("TWITTER_ACCESS_TOKEN", "token")
    monkeypatch.setenv("TWITTER_ACCESS_TOKEN_SECRET", "token-secret")


def test_live_home_timeline_calls_tweepy(monkeypatch):
    _env(monkeypatch)
    fake_client = MagicMock()
    fake_client.get_home_timeline.return_value = SimpleNamespace(
        data=[
            SimpleNamespace(id=11, text="Hello timeline", author_id=99),
        ],
        includes={"users": [SimpleNamespace(id=99, username="alice")]},
    )

    with patch("tweepy.Client", return_value=fake_client):
        live = LiveTwitterClient()
        tweets = live.get_home_timeline(max_results=10)

    fake_client.get_home_timeline.assert_called_once()
    kwargs = fake_client.get_home_timeline.call_args.kwargs
    assert kwargs["user_auth"] is True
    assert kwargs["max_results"] == 10
    assert tweets == [Tweet(id="11", text="Hello timeline", author="alice")]


def test_live_user_timeline_calls_tweepy(monkeypatch):
    _env(monkeypatch)
    fake_client = MagicMock()
    fake_client.get_user.return_value = SimpleNamespace(
        data=SimpleNamespace(id=42, username="nasa")
    )
    fake_client.get_users_tweets.return_value = SimpleNamespace(
        data=[SimpleNamespace(id=7, text="Space is cool")]
    )

    with patch("tweepy.Client", return_value=fake_client):
        live = LiveTwitterClient()
        tweets = live.get_user_timeline("NASA", max_results=5)

    fake_client.get_user.assert_called_once_with(username="NASA")
    fake_client.get_users_tweets.assert_called_once()
    assert tweets[0].text == "Space is cool"
    assert tweets[0].author == "NASA"


def test_live_follow_user_calls_tweepy(monkeypatch):
    _env(monkeypatch)
    fake_client = MagicMock()
    fake_client.get_me.return_value = SimpleNamespace(data=SimpleNamespace(id=1))
    fake_client.get_user.return_value = SimpleNamespace(
        data=SimpleNamespace(id=55, username="learnerbot")
    )

    with patch("tweepy.Client", return_value=fake_client):
        live = LiveTwitterClient()
        message = live.follow_user("learnerbot")

    fake_client.follow_user.assert_called_once_with(
        target_user_id=55, user_auth=True
    )
    assert "learnerbot" in message


def test_live_client_requires_credentials(monkeypatch):
    for key in (
        "TWITTER_BEARER_TOKEN",
        "TWITTER_API_KEY",
        "TWITTER_API_SECRET",
        "TWITTER_ACCESS_TOKEN",
        "TWITTER_ACCESS_TOKEN_SECRET",
    ):
        monkeypatch.delenv(key, raising=False)
    with pytest.raises(RuntimeError, match="credentials missing"):
        with patch("tweepy.Client"):
            LiveTwitterClient()
