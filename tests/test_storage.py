"""Tests for SQLite storage of words and sentence structures."""

from tweet_intelligence.storage.database import Storage


def test_record_and_retrieve_words(tmp_path):
    db = tmp_path / "test.db"
    with Storage(db_path=db) as storage:
        storage.record_words([("python", "NNP"), ("python", "NNP"), ("idea", "NN")])
        words = storage.get_words_by_pos("NNP")
        assert words[0] == ("python", 2)
        all_words = storage.get_all_words()
        assert ("python", "NNP", 2) in all_words
        assert ("idea", "NN", 1) in all_words


def test_record_and_retrieve_structures(tmp_path):
    db = tmp_path / "test.db"
    with Storage(db_path=db) as storage:
        storage.record_structure("PRP VBP JJ NN")
        storage.record_structure("PRP VBP JJ NN")
        storage.record_structure("DT NN VBZ JJ")
        structures = storage.get_structures()
        assert structures[0] == ("PRP VBP JJ NN", 2)
        assert ("DT NN VBZ JJ", 1) in structures


def test_save_tweet_and_counts(tmp_path):
    db = tmp_path / "test.db"
    with Storage(db_path=db) as storage:
        storage.save_tweet("1", "Hello world", author="alice", source="mock")
        storage.save_tweet("1", "Hello world again", author="alice", source="mock")
        assert storage.tweet_count() == 1
        storage.record_word("hello", "UH")
        storage.record_structure("UH NN")
        assert storage.word_count() == 1
        assert storage.structure_count() == 1
