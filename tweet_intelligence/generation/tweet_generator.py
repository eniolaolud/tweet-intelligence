"""Generate tweets by filling learned POS patterns with stored words."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tweet_intelligence.storage.database import Storage


# Fallback patterns so generation still works on a nearly empty database.
_FALLBACK_PATTERNS = [
    "PRP VBP JJ NN",
    "DT NN VBZ JJ",
    "NNP VBZ DT NN",
    "PRP VBD RB JJ",
]

_FALLBACK_WORDS: dict[str, list[str]] = {
    "PRP": ["i", "we", "they", "you"],
    "VBP": ["love", "need", "want", "enjoy"],
    "VBZ": ["is", "feels", "looks", "seems"],
    "VBD": ["found", "built", "shared", "learned"],
    "JJ": ["great", "simple", "curious", "bright"],
    "NN": ["idea", "project", "morning", "pattern"],
    "NNP": ["python", "twitter", "nltk"],
    "DT": ["a", "the", "this"],
    "RB": ["really", "quietly", "often"],
}


class TweetGenerator:
    """Build short tweets from stored words + sentence structures.

    Generation always prefers SQL-backed retrieval:
    1. Sample a sentence structure by stored frequency
    2. For each POS slot, sample a word via indexed ``get_words_by_pos``
    Fallbacks are used only when the database has no matching rows yet.
    """

    def __init__(self, storage: Storage, rng: random.Random | None = None) -> None:
        self.storage = storage
        self.rng = rng or random.Random()

    def generate(self, count: int = 1) -> list[str]:
        count = max(1, count)
        return [self._one() for _ in range(count)]

    def _one(self) -> str:
        pattern = self._pick_pattern()
        tags = pattern.split()
        words = [self._pick_word(tag) for tag in tags]
        tweet = " ".join(words).strip()
        if tweet:
            tweet = tweet[0].upper() + tweet[1:]
        return tweet

    def _pick_pattern(self) -> str:
        structures = self.storage.get_structures(limit=100)
        if structures:
            patterns, weights = zip(*structures)
            return self.rng.choices(list(patterns), weights=list(weights), k=1)[0]
        return self.rng.choice(_FALLBACK_PATTERNS)

    def _pick_word(self, pos: str) -> str:
        # Primary path: efficient indexed retrieval by exact POS tag.
        options = self.storage.get_words_by_pos(pos, limit=100)
        if options:
            words, weights = zip(*options)
            return self.rng.choices(list(words), weights=list(weights), k=1)[0]

        # Secondary path: same POS family (e.g. NN ≈ NNS) via SQL LIKE on pos.
        coarse = pos[:2]
        coarse_matches = self.storage.get_words_by_pos_prefix(coarse, limit=100)
        if coarse_matches:
            words, weights = zip(*coarse_matches)
            return self.rng.choices(list(words), weights=list(weights), k=1)[0]

        fallback = _FALLBACK_WORDS.get(pos) or _FALLBACK_WORDS.get(coarse)
        if fallback:
            return self.rng.choice(fallback)
        return pos.lower()
