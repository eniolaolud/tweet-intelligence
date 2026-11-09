"""Tests for NLTK sentence structure analysis."""

from tweet_intelligence.analysis.nltk_analyzer import Analyzer, clean_tweet_text


def test_clean_tweet_text_strips_urls_and_mentions():
    raw = "Hello @friend check https://example.com #Python rocks!"
    cleaned = clean_tweet_text(raw)
    assert "@friend" not in cleaned
    assert "https" not in cleaned
    assert "Python" in cleaned or "python" in cleaned.lower()
    assert "rocks" in cleaned


def test_analyze_produces_tokens_and_structure():
    analyzer = Analyzer()
    result = analyzer.analyze("I love simple Python projects.")
    assert result.tokens, "expected non-empty tokens"
    assert all(isinstance(word, str) and isinstance(pos, str) for word, pos in result.tokens)
    assert result.structure
    assert len(result.structure.split()) == len(result.tokens)


def test_analyze_empty_text():
    analyzer = Analyzer()
    result = analyzer.analyze("   https://only.a.link  @nobody ")
    assert result.tokens == []
    assert result.structure == ""
