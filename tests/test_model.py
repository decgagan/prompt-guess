"""Integration tests with the real embedding model (downloaded on first run)."""
import sys, pathlib
import pytest
sys.path.insert(0, str(pathlib.Path(__file__).parents[1] / "scoring"))
from prompt_guess_scoring import Scorer

@pytest.fixture(scope="module")
def scorer():
    return Scorer()

ANS = "a golden retriever running on a beach at sunset"

def test_exact_is_100(scorer):
    assert scorer.score(ANS, ANS)["score"] >= 99

def test_unrelated_is_near_zero(scorer):
    assert scorer.score(ANS, "a bowl of ramen noodles")["score"] <= 5

def test_ordering(scorer):
    s = [scorer.score(ANS, g)["score"] for g in
         ["a golden dog running along the seaside at dusk", "a dog on a beach", "a plate of spaghetti"]]
    assert s[0] > s[1] > s[2]

def test_blank_guess(scorer):
    assert scorer.score(ANS, "   ")["score"] == 0

def test_eval_metrics_floor():
    import evaluate
    sc = Scorer()
    m = evaluate.metrics(evaluate.load_features(sc), sc.params)
    assert m["spearman"] >= 0.9 and m["bucket_accuracy"] >= 0.85
