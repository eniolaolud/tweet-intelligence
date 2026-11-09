# Tweet Intelligence Engine

A learner-friendly Python app that:

1. Integrates the **Twitter API** to retrieve timeline data and follow users
2. Analyzes **sentence structure** with **NLTK**
3. Stores encountered **words** and **sentence structures** in **SQL (SQLite)**
4. Generates new tweets from those learned words and patterns

Built as a small, modular project you can read module-by-module. Mock/offline mode works without API keys.

## Project layout

```
tweet_intelligence/
  api/           # Live Twitter API client (tweepy) + mock/offline client
  analysis/      # NLTK tokenization + POS tagging → sentence structures
  storage/       # SQLite persistence for words & structures (indexed retrieval)
  generation/    # Fills learned POS patterns with stored words
  sample_data/   # Offline demo tweets
  cli.py         # Command-line entry point
  engine.py      # Glue: fetch → analyze → store → generate
tests/           # Unit/integration tests (including live-API mocks)
```

## Setup

```bash
git clone https://github.com/eniolaolud/tweet-intelligence.git
cd tweet-intelligence

python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

pip install -r requirements.txt
# or: pip install -e ".[dev]"
```

### Twitter API keys (for live mode)

```bash
cp .env.example .env
```

| Variable | Purpose |
|---|---|
| `TWITTER_BEARER_TOKEN` | Read public user timelines |
| `TWITTER_API_KEY` | OAuth 1.0a (home timeline + follow) |
| `TWITTER_API_SECRET` | OAuth 1.0a |
| `TWITTER_ACCESS_TOKEN` | OAuth 1.0a |
| `TWITTER_ACCESS_TOKEN_SECRET` | OAuth 1.0a |

**Never commit `.env` or hardcode secrets.** Without credentials, the app uses mock/offline mode automatically. Use `--live` to require the real API, or `--mock` to force sample data.

Optional: set `TWEET_INTELLIGENCE_DB` (default `data/tweet_intelligence.db`) — the same file is reused across runs for persistence.

## Resume requirements → how to demo

| # | Requirement | Code path | How to demo |
|---|---|---|---|
| 1 | Twitter API timeline retrieval | `api/twitter_client.py` → `LiveTwitterClient.get_home_timeline` / `get_user_timeline` | `python -m tweet_intelligence --live fetch-timeline` or `... --live fetch-user NASA` |
| 2 | Follow users via Twitter API | `LiveTwitterClient.follow_user` → tweepy `follow_user` | `python -m tweet_intelligence --live follow some_username` |
| 3 | Analyze sentence structure (NLTK) | `analysis/nltk_analyzer.py` | `python -m tweet_intelligence analyze "I love simple Python projects."` |
| 4 | Generate from encountered words/patterns | `generation/tweet_generator.py` reads SQL words + structures | `analyze-demo` then `generate -n 5` |
| 5 | SQL storage for words | `storage/database.py` table `words` | `show-words` after ingest |
| 6 | SQL storage for sentence structures | table `structures` | `show-structures` after ingest |
| 7 | Persistence across runs | SQLite file on disk | Run `analyze-demo`, quit, run `stats` again — counts remain |
| 8 | Efficient retrieval for generation | indexes `idx_words_pos`, `idx_structures_count`; `get_words_by_pos` / `get_structures` | Generation samples via those queries (see tests) |

Offline stand-in for 1–2 (same CLI, sample data): add `--mock`.

## Quick start (no Twitter keys)

```bash
# Load sample tweets → NLTK analysis → SQL store
python -m tweet_intelligence analyze-demo

# Inspect persistence
python -m tweet_intelligence stats
python -m tweet_intelligence show-words --limit 15
python -m tweet_intelligence show-structures

# Analyze one sentence (NLTK POS + structure)
python -m tweet_intelligence analyze "We need clean structure when we store words."
python -m tweet_intelligence analyze "We need clean structure when we store words." --store

# Generate from learned words + patterns
python -m tweet_intelligence generate -n 5
```

## Commands

| Command | What it does |
|---|---|
| `analyze-demo` | Ingest bundled sample tweets (always offline) |
| `analyze TEXT [--store]` | NLTK sentence-structure analysis of one string |
| `fetch-timeline` | Fetch **home timeline** (live API) and learn |
| `fetch-user USERNAME` | Fetch a **user timeline** (live API) and learn |
| `follow USERNAME` | **Follow** a user via Twitter API |
| `generate -n N` | Generate `N` tweets from learned words/patterns |
| `stats` | Show tweet / word / structure counts |
| `show-words [--pos TAG]` | List common stored words |
| `show-structures` | List common POS patterns |

Flags: `--mock` (offline), `--live` (require Twitter API), `--db PATH` (SQLite file).

### Live Twitter examples

```bash
python -m tweet_intelligence --live fetch-user NASA --limit 10
python -m tweet_intelligence --live fetch-timeline --limit 10
python -m tweet_intelligence --live follow some_username
python -m tweet_intelligence generate -n 3
```

### Forced mock mode

```bash
python -m tweet_intelligence --mock fetch-timeline
python -m tweet_intelligence --mock follow learnerbot
```

## How it works (short)

1. **API** — `create_client()` returns `LiveTwitterClient` (tweepy) when credentials exist, otherwise `MockTwitterClient` (`sample_data/sample_tweets.json`).
2. **Analysis** — NLTK tokenizes and POS-tags each tweet. The tag sequence (e.g. `PRP VBP JJ NN`) is the sentence structure.
3. **Storage** — SQLite tables `words (word, pos, count)` and `structures (pattern, count)`, with indexes for POS/frequency lookups. Data survives process restarts.
4. **Generation** — Sample a structure by frequency, then fill each POS slot with a weighted word from `get_words_by_pos` (indexed).

## Tests

```bash
pytest -q
```

Includes live-API unit tests that mock tweepy (no network), plus persistence and retrieval tests.

## License

MIT (learning / portfolio project).
