"""Evaluate the scorer on eval.csv: Spearman correlation and bucket accuracy.

    python scoring/evaluate.py            # evaluate with saved params.json
    python scoring/evaluate.py --tune     # grid-search params, save, then evaluate
"""
from __future__ import annotations

import argparse
import itertools
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

sys.path.insert(0, str(Path(__file__).parent))
from prompt_guess_scoring import Scorer, Params, combine, bucket, keyword_match  # noqa: E402

EVAL = Path(__file__).with_name("eval.csv")
ORDER = {"miss": 0, "partial": 1, "close": 2, "great": 3}


def load_features(scorer: Scorer) -> pd.DataFrame:
    df = pd.read_csv(EVAL, comment="#")
    a = scorer.embed(df.answer.tolist())
    g = scorer.embed(df.guess.tolist())
    df["cosine"] = (a * g).sum(axis=1)
    kw = [keyword_match(x, y) for x, y in zip(df.answer, df.guess)]
    df["kw"] = [k[0] for k in kw]
    df["matched"] = [k[1] for k in kw]
    df["target"] = df.expected.map(ORDER)
    return df


def metrics(df: pd.DataFrame, p: Params) -> dict:
    scores = np.array([combine(c, k, p) for c, k in zip(df.cosine, df.kw)])
    preds = [bucket(s, p) for s in scores]
    rho = spearmanr(scores, df.target).statistic
    acc = float(np.mean([pr == ex for pr, ex in zip(preds, df.expected)]))
    off1 = float(np.mean([abs(ORDER[pr] - ORDER[ex]) <= 1 for pr, ex in zip(preds, df.expected)]))
    return {"spearman": float(rho), "bucket_accuracy": acc, "within_one_bucket": off1,
            "scores": scores, "preds": preds}


def fit_thresholds(scores, df):
    """Pick thresholds as midpoints between neighbouring buckets' median scores, then refine."""
    best, best_acc = None, -1
    grid = range(5, 100, 5)
    for p_, c_, g_ in itertools.combinations(grid, 3):
        t = {"partial": p_, "close": c_, "great": g_}
        pred = np.where(scores >= g_, 3, np.where(scores >= c_, 2, np.where(scores >= p_, 1, 0)))
        acc = float(np.mean(pred == df.target.values))
        if acc > best_acc:
            best, best_acc = t, acc
    return best, best_acc


def tune(df: pd.DataFrame) -> Params:
    best, best_obj = None, -1
    for lo in np.arange(0.40, 0.71, 0.025):
        for hi in np.arange(0.85, 1.001, 0.025):
            for gamma in (0.7, 1.0, 1.3):
                for w in (0.0, 0.1, 0.2, 0.3, 0.4):
                    p = Params(cos_lo=round(lo, 3), cos_hi=round(hi, 3), gamma=gamma, kw_weight=w)
                    scores = np.array([combine(c, k, p) for c, k in zip(df.cosine, df.kw)])
                    t, acc = fit_thresholds(scores, df)
                    rho = spearmanr(scores, df.target).statistic
                    # Also reward a sensible scale: exact paraphrase ~ high, unrelated ~ 0.
                    miss_mean = scores[df.target.values == 0].mean()
                    great_mean = scores[df.target.values == 3].mean()
                    scale = (great_mean - miss_mean) / 100
                    obj = acc + 0.5 * rho + 0.25 * scale
                    if obj > best_obj:
                        p.thresholds = t
                        best, best_obj = p, obj
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tune", action="store_true")
    ap.add_argument("--cv", action="store_true", help="grouped 4-fold cross-validation (held-out answers)")
    ap.add_argument("--show", action="store_true", help="print every pair")
    args = ap.parse_args()
    scorer = Scorer()
    df = load_features(scorer)
    if args.tune:
        base = metrics(df, Params())
        print(f"before tuning (defaults): spearman={base['spearman']:.3f} acc={base['bucket_accuracy']:.3f}")
        p = tune(df)
        p.save()
        scorer.params = p
        print("tuned params:", p)
    if args.cv:
        answers = df.answer.unique()
        accs, rhos = [], []
        for k in range(4):
            test = set(answers[k::4])
            tr, te = df[~df.answer.isin(test)], df[df.answer.isin(test)]
            m_ = metrics(te, tune(tr))
            accs.append(m_["bucket_accuracy"]); rhos.append(m_["spearman"])
        print(f"4-fold CV on held-out answers: spearman={np.mean(rhos):.3f} bucket_accuracy={np.mean(accs):.3f}")
    p = scorer.params
    m = metrics(df, p)
    print(f"n={len(df)}  spearman={m['spearman']:.3f}  bucket_accuracy={m['bucket_accuracy']:.3f}  "
          f"within_one_bucket={m['within_one_bucket']:.3f}")
    print("mean score by expected bucket:")
    print(pd.Series(m["scores"]).groupby(df.expected).mean().reindex(list(ORDER)).round(1).to_string())
    print("confusion (rows=expected, cols=predicted):")
    print(pd.crosstab(df.expected, pd.Series(m["preds"], name="pred")).reindex(index=list(ORDER), columns=list(ORDER), fill_value=0))
    if args.show:
        for (_, r), s, pr in zip(df.iterrows(), m["scores"], m["preds"]):
            flag = "" if pr == r.expected else "  <-- " + pr
            print(f"{s:5.1f} [{r.expected:7}] {r.guess!r} vs {r.answer!r}{flag}")
    return m


if __name__ == "__main__":
    main()
