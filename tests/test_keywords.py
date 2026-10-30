import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parents[1] / "scoring"))
from prompt_guess_scoring import keyword_match, canonical, content_words, combine, bucket, Params


def test_stopwords_dropped():
    assert content_words("a dog on the beach") == ["dog", "beach"]

def test_lemmas_and_synonyms():
    assert canonical("puppies") == canonical("dog")
    assert canonical("kittens") == "cat"
    assert canonical("running") == canonical("run")
    assert canonical("seaside") == canonical("beach")

def test_keyword_match():
    r, m = keyword_match("a golden retriever running on a beach", "dog runs by the sea")
    assert set(m) == {"running", "beach"}
    assert 0 < r < 1

def test_empty():
    assert keyword_match("", "anything") == (0.0, [])

def test_combine_bounds_and_buckets():
    p = Params()
    assert combine(0.0, 0.0, p) == 0
    assert combine(1.0, 1.0, p) == 100
    assert bucket(100, p) == "great" and bucket(0, p) == "miss"
