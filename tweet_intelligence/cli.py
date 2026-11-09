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
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Force offline/demo mode (sample data, no Twitter credentials needed).",
    )
    parser.add_argument(
        "--db",
        default=None,
        help="SQLite database path (default: data/tweet_intelligence.db).",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    fetch = sub.add_parser("fetch-timeline", help="Fetch home timeline and learn from it.")
    fetch.add_argument("--limit", type=int, default=20, help="Max tweets to fetch (default 20).")

    user = sub.add_parser("fetch-user", help="Fetch a user's recent tweets and learn from them.")
    user.add_argument("username", help="Twitter username (with or without @).")
    user.add_argument("--limit", type=int, default=20, help="Max tweets to fetch (default 20).")

    follow = sub.add_parser("follow", help="Follow a Twitter user.")
    follow.add_argument("username", help="Twitter username (with or without @).")

    analyze = sub.add_parser(
        "analyze-demo",
        help="Load sample tweets, analyze them, and store words/structures (always offline).",
    )

    gen = sub.add_parser("generate", help="Generate tweets from learned words and patterns.")
    gen.add_argument("-n", "--count", type=int, default=3, help="How many tweets to generate.")

    sub.add_parser("stats", help="Show counts of stored tweets, words, and structures.")

    show = sub.add_parser("show-structures", help="Print the most common sentence structures.")
    show.add_argument("--limit", type=int, default=10)

    words = sub.add_parser("show-words", help="Print the most common stored words.")
    words.add_argument("--limit", type=int, default=20)
    words.add_argument("--pos", default=None, help="Optional POS filter, e.g. NN or JJ.")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    from tweet_intelligence.storage.database import Storage

    storage = Storage(db_path=args.db) if args.db else Storage()

    # analyze-demo always uses mock sample data.
    mock_flag: bool | None
    if args.command == "analyze-demo":
        mock_flag = True
    elif args.mock:
        mock_flag = True
    else:
        mock_flag = None

    engine = TweetIntelligenceEngine(storage=storage, mock=mock_flag)

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
            rows = [(w, args.pos, c) for w, c in storage.get_words_by_pos(args.pos, limit=args.limit)]
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
