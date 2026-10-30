# Prompt Guess

*(working name)* A daily guessing game: everyone sees the same AI-generated image, and has **five guesses** to work out the prompt that made it. Each guess is scored **0–100 on how close its meaning is**, and the key words you hit are revealed as you go. Finish and share a spoiler-free emoji grid, Wordle-style.

## Status

**Milestone 1 (scoring engine): done.** Current scorer: **v3** (v2 synonym groups with v1 weights). See [`scoring/`](scoring/README.md).

| Metric (scorer v3) | Value |
|---|---|
| eval.csv Spearman (64 synthetic pairs) | 0.968 |
| eval.csv bucket accuracy | 95.3% |
| vs Dec's 12 hand ratings: mean absolute error | 6.1 |
| vs Dec's 12 hand ratings: Spearman | 0.943 |
| vs Dec's 12 hand ratings: same bucket | 12/12 |

```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
cd scoring && python -m prompt_guess_scoring "a dog on a beach at sunset" "puppy by the sea"
python evaluate.py --show      # metrics + every pair
python evaluate.py --tune --cv # re-fit the calibration
pytest -q
```

## Plan

- **Front end:** Svelte + Vite on Cloudflare Pages.
- **Scoring:** a Cloudflare Worker using Workers AI `@cf/baai/bge-small-en-v1.5`, the same model as the Python prototype, so the calibration carries over.
- **Puzzles:** prompts and images generated ahead of time and checked by hand; answers stay server-side.
- **Progress:** streaks kept in the browser; no accounts.

## Milestones

1. ✅ **Scoring engine:** embeddings + calibrated 0–100 + keyword hits, with an eval set, metrics and tuning.
2. **First 30 puzzles:** prompts, images, quality and safety checks.
3. **Playable game:** guess input, score bar, keyword reveals, share grid.
4. **Launch:** domain, streaks, stats, "how scoring works" page, screenshots.
5. **Extras:** unlimited practice mode, archive, anonymous "most common wrong guess" stats.

Rules for content: no adult content, no real people's faces.

## Licence

MIT
