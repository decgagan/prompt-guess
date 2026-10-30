"""Where the puzzle data lives. The real puzzles (answers, images, puzzle synonyms) are in the
private repo decgagan/prompt-guess-puzzles; this public repo ships only a fake sample.

Resolution order: $PUZZLES_DIR, then a `prompt-guess-puzzles` checkout next to this repo,
then `puzzles-sample/` in this repo.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SAMPLE = REPO / "puzzles-sample"


def puzzles_dir() -> Path:
    if os.environ.get("PUZZLES_DIR"):
        return Path(os.environ["PUZZLES_DIR"]).resolve()
    sibling = REPO.parent / "prompt-guess-puzzles"
    return sibling if (sibling / "puzzles.json").is_file() else SAMPLE


def load_puzzles() -> list[dict]:
    return json.loads((puzzles_dir() / "puzzles.json").read_text())


def load_synonym_groups() -> list[list[str]]:
    f = puzzles_dir() / "synonyms.json"
    return json.loads(f.read_text()) if f.is_file() else []
