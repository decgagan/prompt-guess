import datetime
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUZZLES = json.loads((ROOT / "puzzles" / "puzzles.json").read_text())


def test_thirty_puzzles_with_unique_ids_and_dates():
    assert len(PUZZLES) == 30
    assert len({p["id"] for p in PUZZLES}) == len(PUZZLES)
    dates = [datetime.date.fromisoformat(p["date"]) for p in PUZZLES]
    assert len(set(dates)) == len(dates)
    assert dates == sorted(dates)


def test_every_puzzle_has_an_existing_small_image():
    for p in PUZZLES:
        assert p["image"], p["id"]
        f = ROOT / p["image"]
        assert f.is_file(), f
        assert f.stat().st_size < 200_000, f


def test_fields_and_alt_text_does_not_leak_answer():
    for p in PUZZLES:
        assert p["difficulty"] in {"easy", "medium", "hard"}
        assert 6 <= len(p["prompt"].split()) <= 14
        assert p["alt"] and p["prompt"].lower() not in p["alt"].lower()
        assert p["gen_prompt"].startswith(p["prompt"])
