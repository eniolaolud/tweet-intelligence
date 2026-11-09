"""Analyze tweets into words + POS tags and sentence structure patterns."""

from __future__ import annotations

from dataclasses import dataclass
import re


@dataclass(frozen=True)
class AnalysisResult:
    """One tweet broken into tokens and a POS pattern string."""

    tokens: list[tuple[str, str]]  # (word, POS)
    structure: str  # e.g. "PRP VBP JJ NN"


_URL_RE = re.compile(r"https?://\S+|www\.\S+")
_MENTION_RE = re.compile(r"@\w+")
_HASHTAG_RE = re.compile(r"#(\w+)")
_NON_WORD_RE = re.compile(r"[^\w\s']+", re.UNICODE)


def _ensure_nltk() -> None:
    """Download lightweight NLTK models on first use."""
    import nltk

    for resource in ("punkt", "punkt_tab", "averaged_perceptron_tagger", "averaged_perceptron_tagger_eng"):
        try:
            nltk.data.find(
                {
                    "punkt": "tokenizers/punkt",
                    "punkt_tab": "tokenizers/punkt_tab",
                    "averaged_perceptron_tagger": "taggers/averaged_perceptron_tagger",
                    "averaged_perceptron_tagger_eng": "taggers/averaged_perceptron_tagger_eng",
                }[resource]
            )
        except LookupError:
            nltk.download(resource, quiet=True)


def clean_tweet_text(text: str) -> str:
    """Strip URLs/mentions and normalize hashtags for cleaner POS tagging."""
    text = _URL_RE.sub(" ", text)
    text = _MENTION_RE.sub(" ", text)
    text = _HASHTAG_RE.sub(r"\1", text)
    text = _NON_WORD_RE.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip()


class Analyzer:
    """NLTK sentence/structure analyzer."""

    def __init__(self) -> None:
        _ensure_nltk()

    def analyze(self, text: str) -> AnalysisResult:
        from nltk import pos_tag, word_tokenize

        cleaned = clean_tweet_text(text)
        if not cleaned:
            return AnalysisResult(tokens=[], structure="")

        words = word_tokenize(cleaned)
        # Keep alphabetic tokens (and contractions with apostrophes).
        words = [w for w in words if any(c.isalpha() for c in w)]
        if not words:
            return AnalysisResult(tokens=[], structure="")

        tagged = pos_tag(words)
        # Normalize to lowercase words; keep NLTK POS tags as structure atoms.
        tokens = [(word.lower(), tag) for word, tag in tagged]
        structure = " ".join(tag for _, tag in tokens)
        return AnalysisResult(tokens=tokens, structure=structure)

    def analyze_many(self, texts: list[str]) -> list[AnalysisResult]:
        return [self.analyze(text) for text in texts]
