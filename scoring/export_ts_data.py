"""Export the keyword tables and a parity fixture for the TypeScript port in web/server/.

python scoring/export_ts_data.py            # tables only (fast, no model)
python scoring/export_ts_data.py --fixture  # + expected scores from the Python scorer
"""
import csv, json, sys
from pathlib import Path
HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
from prompt_guess_scoring import keywords as K

OUT = HERE.parent / "web" / "server"
tables = {"stopwords": sorted(K.STOPWORDS), "synonyms_v1": K.SYNONYMS, "synonyms_v2": K.SYNONYMS_V2,
          "irregular": K._IRREGULAR}
(OUT / "keywords.json").write_text(json.dumps(tables, indent=1, sort_keys=True) + "\n")
print("wrote", OUT / "keywords.json")

if "--fixture" in sys.argv:
    from prompt_guess_scoring.scorer import Scorer
    s = Scorer()
    rows = lambda f: list(csv.DictReader(l for l in open(HERE / f) if not l.startswith("#")))
    pairs = [("eval", r["answer"], r["guess"]) for r in rows("eval.csv")]
    pairs += [("dec", r["answer"], r["guess"]) for r in rows("human_ratings.csv")]
    fx = []
    for src, a, g in pairs:
        r = s.score(a, g)
        fx.append({"source": src, "answer": a, "guess": g, "cosine": float(s.cosine(a, g)),
                   "score": r["score"], "bucket": r["bucket"], "matched": r["matched"]})
    (HERE.parent / "web" / "test" / "parity_fixture.json").write_text(json.dumps(fx, indent=1) + "\n")
    print("fixture pairs:", len(fx))
