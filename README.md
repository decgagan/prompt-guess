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

**Milestone 2 (first 30 puzzles): done.** `puzzles/puzzles.json` holds 30 puzzles (10 easy, 12 medium, 8 hard), one a day from 2026-11-09, with 1024px WebP images in `puzzles/images/`. Each image was checked by eye; four were regenerated because they contained text that gave the answer away. `gen_prompt` is the exact text sent to the image model (the answer plus a "no text" instruction).

> **Answers stay server-side.** `puzzles.json` contains the answers, so it must never be imported into the front-end bundle. The client gets only the date, image and alt text; the Worker reads the prompt and scores guesses.

**Milestone 3 (playable game): done.** [`web/`](web/) is a Svelte 5 + Vite app with Cloudflare Pages Functions in `web/functions/api/`:

- `GET /api/today`: today's puzzle by UK date (number, alt text, image URL, blanked prompt). No answer.
- `POST /api/guess {date, guess}`: score 0–100, bucket, matched words and their positions in the prompt. Only today's or past puzzles.
- `POST /api/reveal {date, guesses}`: the full prompt, only once the game is over (5 guesses, a winning last guess re-scored on the server, or a past puzzle).
- `GET /api/image?date=`: the image for a playable date. Images are built to unguessable hashed names (`IMAGE_SALT`), so future images can't be listed or fetched.
- Light per-IP rate limit (30 req/min, per isolate).

`web/server/scoring.ts` is a straight TypeScript port of scorer v3 (keyword lemmas, v2 synonyms, calibration from `params.json`). `npm test` checks it against Python-computed scores for all 76 eval + hand-rated pairs (they match to ±0.0, same bucket 76/76), and checks that no answer is in the built bundle (`npm run build` also fails if one is).

> **Parity note:** the fixture uses the cosines from the local Python model. Live Workers AI embeddings for `bge-small-en-v1.5` may differ slightly (quantisation/runtime), so live scores can be a point or so away from the Python prototype.

### Run locally

```bash
# 1. embedding server (the Python model stands in for Workers AI)
python scoring/embed_server.py            # http://127.0.0.1:8789
# 2. the app + functions
cd web && npm install
cp .dev.vars.example .dev.vars            # EMBED_URL and FAKE_TODAY=2026-11-09
npm run build && npm run pages:dev        # http://localhost:8788
npm test                                  # parity + dist leak tests
npm run play                              # Playwright plays a game on desktop + mobile
```

`npm run dev` (Vite on :5173) proxies `/api` to `pages:dev` for hot reload.

### Deploy (not done yet)

1. Cloudflare dashboard → Pages → connect the repo. Root directory `web`, build command `npm run build`, output `dist`.
2. Set `IMAGE_SALT` to a long random string as a **build** variable and as a **secret** for the functions. The two must match.
3. The Workers AI binding `AI` is declared for production and preview in `web/wrangler.toml`. It is left out of local dev so no Cloudflare login is needed.
4. Add the custom domain.

## Plan

- **Front end:** Svelte + Vite on Cloudflare Pages.
- **Scoring:** a Cloudflare Worker using Workers AI `@cf/baai/bge-small-en-v1.5`, the same model as the Python prototype, so the calibration carries over.
- **Puzzles:** prompts and images generated ahead of time and checked by hand; answers stay server-side.
- **Progress:** streaks kept in the browser; no accounts.

## Milestones

1. ✅ **Scoring engine:** embeddings + calibrated 0–100 + keyword hits, with an eval set, metrics and tuning.
2. ✅ **First 30 puzzles:** prompts, images, quality and safety checks. See [`puzzles/`](puzzles/).
3. ✅ **Playable game:** guess input, score bar, keyword reveals, share grid.
4. **Launch:** domain, streaks, stats, "how scoring works" page, screenshots.
5. **Extras:** unlimited practice mode, archive, anonymous "most common wrong guess" stats.

Rules for content: no adult content, no real people's faces.

## Licence

MIT
