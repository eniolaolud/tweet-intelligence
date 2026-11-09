"""Command-line interface for the Tweet Intelligence Engine."""

from __future__ import annotations

import argparse
import sys

from tweet_intelligence.engine import TweetIntelligenceEngine


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tweet-intelligence",
        description=(
            "Learn words and sentence structures from tweets, "
            "then generate new tweets from those patterns."
        ),
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--mock",
        action="store_true",
        help="Force offline/demo mode (sample data, no Twitter credentials needed).",
    )
    mode.add_argument(
        "--live",
        action="store_true",
        help="Force live Twitter API mode (requires credentials in env / .env).",
    )
    parser.add_argument(
        "--db",
        default=None,
        help="SQLite database path (default: data/tweet_intelligence.db).",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    fetch = sub.add_parser(
        "fetch-timeline",
        help="Fetch home timeline via Twitter API and learn from it.",
    )
    fetch.add_argument("--limit", type=int, default=20, help="Max tweets to fetch (default 20).")

    user = sub.add_parser(
        "fetch-user",
        help="Fetch a user's timeline via Twitter API and learn from it.",
    )
    user.add_argument("username", help="Twitter username (with or without @).")
    user.add_argument("--limit", type=int, default=20, help="Max tweets to fetch (default 20).")

    follow = sub.add_parser(
        "follow",
        help="Follow a Twitter user via the Twitter API (OAuth user context required).",
    )
    follow.add_argument("username", help="Twitter username (with or without @).")

    analyze = sub.add_parser(
        "analyze",
        help="Analyze sentence structure of text with NLTK (optionally persist words/patterns).",
    )
    analyze.add_argument("text", help="Sentence or tweet text to analyze.")
    analyze.add_argument(
        "--store",
        action="store_true",
        help="Persist encountered words and the sentence structure into SQLite.",
    )

    demo = sub.add_parser(
        "analyze-demo",
        help="Load sample tweets, analyze them, and store words/structures (always offline).",
    )

    gen = sub.add_parser(
        "generate",
        help="Generate tweets from encountered words and learned sentence structures.",
    )
    gen.add_argument("-n", "--count", type=int, default=3, help="How many tweets to generate.")

    sub.add_parser("stats", help="Show counts of stored tweets, words, and structures.")

    show = sub.add_parser("show-structures", help="Print the most common sentence structures.")
    show.add_argument("--limit", type=int, default=10)

    words = sub.add_parser("show-words", help="Print the most common stored words.")
    words.add_argument("--limit", type=int, default=20)
    words.add_argument("--pos", default=None, help="Optional POS filter, e.g. NN or JJ.")

    return parser


def _resolve_mock_flag(args: argparse.Namespace) -> bool | None:
    if args.command == "analyze-demo":
        return True
    if args.mock:
        return True
    if args.live:
        return False
    return None


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    from tweet_intelligence.storage.database import Storage

    storage = Storage(db_path=args.db) if args.db else Storage()
    engine = TweetIntelligenceEngine(storage=storage, mock=_resolve_mock_flag(args))

    if args.command == "fetch-timeline":
        n = engine.fetch_timeline(max_results=args.limit)
        print(f"Ingested {n} timeline tweet(s).")
        _print_stats(engine)
        return 0

    if args.command == "fetch-user":
        n = engine.fetch_user(args.username, max_results=args.limit)
        print(f"Ingested {n} tweet(s) from @{args.username.lstrip('@')}.")
        _print_stats(engine)
        return 0

    if args.command == "follow":
        message = engine.follow(args.username)
        print(message)
        return 0

    if args.command == "analyze":
        result = engine.analyze_text(args.text, persist=args.store)
        tokens = result["tokens"]
        structure = result["structure"]
        if not tokens:
            print("No analyzable words found in that text.")
            return 0
        print("Tokens (word / POS):")
        for word, pos in tokens:  # type: ignore[misc]
            print(f"  {word:20s}  {pos}")
        print(f"Sentence structure: {structure}")
        if args.store:
            print("Stored words and structure in SQLite.")
            _print_stats(engine)
        return 0

    if args.command == "analyze-demo":
        n = engine.fetch_timeline(max_results=50)
        print(f"Analyzed and stored {n} sample tweet(s) (mock mode).")
        _print_stats(engine)
        return 0

    if args.command == "generate":
        tweets = engine.generate(count=args.count)
        for i, text in enumerate(tweets, start=1):
            print(f"{i}. {text}")
        return 0

    if args.command == "stats":
        _print_stats(engine)
        return 0

    if args.command == "show-structures":
        rows = storage.get_structures(limit=args.limit)
        if not rows:
            print("No structures stored yet. Run: python -m tweet_intelligence analyze-demo")
            return 0
        for pattern, count in rows:
            print(f"{count:4d}  {pattern}")
        return 0

    if args.command == "show-words":
        if args.pos:
            rows = [
                (w, args.pos, c)
                for w, c in storage.get_words_by_pos(args.pos, limit=args.limit)
            ]
        else:
            rows = storage.get_all_words(limit=args.limit)
        if not rows:
            print("No words stored yet. Run: python -m tweet_intelligence analyze-demo")
            return 0
        for word, pos, count in rows:
            print(f"{count:4d}  {pos:6s}  {word}")
        return 0

    parser.error(f"Unknown command: {args.command}")
    return 2


def _print_stats(engine: TweetIntelligenceEngine) -> None:
    stats = engine.stats()
    print(
        f"Stats — tweets: {stats['tweets']}, "
        f"words: {stats['words']}, "
        f"structures: {stats['structures']}"
    )


if __name__ == "__main__":
    sys.exit(main())
