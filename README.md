# Tweet Intelligence Engine

A learner-friendly Python app that:

1. Pulls tweets from the Twitter API (or sample data offline)
2. Analyzes sentence structure with **NLTK**
3. Stores words and POS patterns in **SQLite**
4. Generates new tweets from what it has learned

Built as a small, modular project you can read module-by-module.

## Project layout

```
tweet_intelligence/
  api/           # Twitter client (live + mock)
  analysis/      # NLTK tokenization + POS tagging
  storage/       # SQLite persistence for words & structures
  generation/    # Pattern-based tweet generation
  sample_data/   # Offline demo tweets
  cli.py         # Command-line entry point
  engine.py      # Glue: fetch → analyze → store → generate
tests/           # Basic unit/integration tests
```

## Setup

```bash
# Clone and enter the repo
git clone https://github.com/eniolaolud/tweet-intelligence.git
cd tweet-intelligence

# Create a virtualenv (recommended)
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Twitter API keys (optional)

Copy the example env file and fill in credentials from the [Twitter Developer Portal](https://developer.twitter.com/):

```bash
cp .env.example .env
```

| Variable | Purpose |
|---|---|
| `TWITTER_BEARER_TOKEN` | Read public user timelines |
| `TWITTER_API_KEY` | OAuth 1.0a (needed for home timeline + follow) |
| `TWITTER_API_SECRET` | OAuth 1.0a |
| `TWITTER_ACCESS_TOKEN` | OAuth 1.0a |
| `TWITTER_ACCESS_TOKEN_SECRET` | OAuth 1.0a |

**Never commit `.env` or hardcode secrets.** Without credentials, the app automatically uses mock/offline mode.

Optional: set `TWEET_INTELLIGENCE_DB` to change the SQLite path (default `data/tweet_intelligence.db`).

## Quick start (no Twitter keys)

```bash
# Load sample tweets, analyze sentence structure, store words/patterns
python -m tweet_intelligence analyze-demo

# Generate tweets from what was learned
python -m tweet_intelligence generate -n 5

# Inspect stored data
python -m tweet_intelligence stats
python -m tweet_intelligence show-words --limit 15
python -m tweet_intelligence show-structures
```

## Commands

All commands accept `--mock` to force offline sample data, and `--db PATH` for a custom database file.

| Command | What it does |
|---|---|
| `analyze-demo` | Ingest bundled sample tweets (always offline) |
| `fetch-timeline` | Fetch home timeline and learn from it |
| `fetch-user USERNAME` | Fetch a user's tweets and learn from them |
| `follow USERNAME` | Follow a user (live) / record follow (mock) |
| `generate -n N` | Generate `N` tweets from learned patterns |
| `stats` | Show tweet / word / structure counts |
| `show-words [--pos TAG]` | List common stored words |
| `show-structures` | List common POS patterns |

### Live Twitter examples

```bash
# Requires credentials in .env
python -m tweet_intelligence fetch-user NASA --limit 10
python -m tweet_intelligence fetch-timeline --limit 10
python -m tweet_intelligence follow some_username
python -m tweet_intelligence generate -n 3
```

### Forced mock mode (even if credentials exist)

```bash
python -m tweet_intelligence --mock fetch-timeline
python -m tweet_intelligence --mock follow learnerbot
```

## How it works (short)

1. **API** — `create_client()` returns a live tweepy client when env vars are set, otherwise a `MockTwitterClient` that reads `sample_data/sample_tweets.json`.
2. **Analysis** — NLTK tokenizes each tweet and POS-tags it. The tag sequence (e.g. `PRP VBP JJ NN`) is the sentence *structure*.
3. **Storage** — Words `(word, pos, count)` and structures `(pattern, count)` live in SQLite for fast weighted retrieval.
4. **Generation** — Pick a structure by frequency, then fill each POS slot with a weighted random word that matches that tag.

## Tests

```bash
pytest -q
```

## License

MIT (learning / portfolio project).
