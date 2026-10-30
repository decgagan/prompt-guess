# Prompt Guess

A daily guessing game. Everyone sees the same AI-generated image and has **five guesses** at the prompt that made it. Each guess is scored **0–100 on how close its meaning is**, not on exact wording, and the key words you hit are revealed as you go. At the end you can share a spoiler-free emoji grid, Wordle-style.

**Play:** <https://prompt-guess.pages.dev> (the first puzzle goes up on **9 November 2026**, UK time).

A portfolio project by Dec, a data science student. The interesting part is the scorer: turning "how close is this guess?" into a number that agrees with people.

## How scoring works

Scorer **v3** (`scoring/prompt_guess_scoring/params.json`):

1. **Meaning (80%).** The guess and the prompt are embedded with [`BAAI/bge-small-en-v1.5`](https://huggingface.co/BAAI/bge-small-en-v1.5) (384 dimensions) and compared with cosine similarity. Live, the same model runs on Cloudflare Workers AI as `@cf/baai/bge-small-en-v1.5`, so the calibration carries over.
2. **Calibration.** With this model even unrelated sentences reach a cosine of about 0.4–0.5, so the cosine is mapped linearly onto 0–100: **0.55 or below is 0, 0.90 or above is 100**.
3. **Key words (20%).** Content words (stopwords removed) are reduced to a base form and to a canonical word from hand-made synonym groups (for example puppy = dog). The share of the prompt's key words the guess hits is added in, and the matched words are revealed in the game.
4. **Buckets.** 85+ **great**, 50+ **close**, 5+ **partial**, below that a **miss**.

## Evaluation

`scoring/eval.csv` holds 64 hand-written pairs (16 prompts × 4 guesses, one per bucket). It is synthetic test data, not real player guesses. `evaluate.py --tune` grid-searches the cosine range, keyword weight and thresholds.

| Scorer v3 | Value |
|---|---|
| eval.csv Spearman | 0.968 |
| eval.csv bucket accuracy | 95.3% |
| 4-fold CV on unseen prompts (tuned) | Spearman 0.969, 92.2% buckets |
| vs Dec's 12 hand ratings: mean absolute error | 6.1 |
| vs Dec's 12 hand ratings: Spearman | 0.943 |
| vs Dec's 12 hand ratings: same bucket | 12/12 |

**Human rating test.** Dec scored 12 pairs by hand (`scoring/human_ratings.csv`). The scorer was then iterated:

- **v1:** tuned on eval.csv. Matched all 12 of Dec's buckets, but was a bit stingy with broader or similar words ("spaceman" for "astronaut"). MAE 7.0.
- **v2:** more synonym groups, 85/15 weighting and a cosine ceiling of 0.89. Closer to Dec (MAE 6.0) but bucket accuracy on eval.csv fell to 90.6%.
- **v3:** the halfway option: v2's synonyms with v1's weights. It keeps v1's eval scores and most of v2's gain against Dec (MAE 6.1). v1 and v2 are kept as `params_v1.json` and `params_v2.json`.

Nothing was fitted to Dec's 12 pairs. Full details are in [`scoring/README.md`](scoring/README.md).

**Python/TypeScript parity.** The live scorer (`web/server/scoring.ts`) is a port of the Python one. `npm test` checks it against Python-computed scores for all 76 eval and hand-rated pairs: identical scores, same bucket 76/76. On the live site, Workers AI embeddings differ very slightly from the local model. In a spot check of five guesses, live scores were within about 3 points of Python, always in the same bucket.

**Limitations:** the eval set is small and written by one person, the synonym table is short, and embeddings can't always tell opposites apart ("a happy dog" vs "a sad dog").

## Architecture

- **Front end:** Svelte 5 + Vite, served by Cloudflare Pages. Progress is kept in the browser; there are no accounts.
- **API:** Cloudflare Pages Functions in `web/functions/api/`, with shared code in `web/server/`:
  - `GET /api/today`: today's puzzle by UK date (number, alt text, image URL, blanked prompt mask). No answer.
  - `POST /api/guess {date, guess}`: score, bucket and matched words. Only today's or past puzzles.
  - `POST /api/reveal {date, guesses}`: the full prompt, only once the game is over.
  - `GET /api/image?date=`: the image for a playable date.
- **Rate limiting:** 30 requests a minute per IP (per isolate).
- **Salted image names:** images are built to hashed names using `IMAGE_SALT`, so future images can't be guessed or listed.
- **Leak check:** `npm run build` runs `scripts/check-dist.mjs`, which fails the build if any answer is in the client bundle. `test/dist.test.ts` checks it again.

## Why the puzzles are in a private repo

The code is public but the answers can't be. The 30 real puzzles (prompts, images and puzzle-specific synonyms) live in the private repo `decgagan/prompt-guess-puzzles`. This repo's history has been rewritten so that no puzzle data appears in it.

Puzzles are loaded from `$PUZZLES_DIR`. If that isn't set, it uses a `prompt-guess-puzzles` checkout next to this repo, and failing that [`puzzles-sample/`](puzzles-sample/), which has three fake puzzles in the same format. Tests, CI and local dev work without the private data.

## Run locally

```bash
# Python scorer
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
cd scoring && python -m prompt_guess_scoring "a dog on a beach at sunset" "puppy by the sea"
python evaluate.py --show        # metrics and every pair
cd ..

# Game: the Python model stands in for Workers AI
python scoring/embed_server.py   # http://127.0.0.1:8789
cd web && npm install
cp .dev.vars.example .dev.vars   # EMBED_URL, and FAKE_TODAY to pretend it's a puzzle day
npm run build && npm run pages:dev   # http://localhost:8788
```

`npm run dev` (Vite on :5173) proxies `/api` to `pages:dev` for hot reload. `FAKE_TODAY` is for local dev only; production uses the real UK date.

## Tests and CI

- `pytest -q`: keyword, model and puzzle-format tests.
- `python scoring/evaluate.py`: scorer metrics.
- `cd web && npm test`: Python/TS parity and the bundle leak check.
- `npm run play`: Playwright plays a full game on desktop and mobile.

The [`CI`](.github/workflows/ci.yml) workflow runs the Python tests, the evaluation, the web build and `npm test` on every push and pull request, using the sample puzzles.

## Deploy

Cloudflare Pages doesn't build from this repo, because it would only see the sample puzzles. Instead the [`Deploy`](.github/workflows/deploy.yml) workflow runs on every push to `main`:

1. It checks out this repo, and the private puzzles repo using a **read-only deploy key** (`PUZZLES_DEPLOY_KEY`).
2. It builds with the real puzzles and `IMAGE_SALT`, so the leak check runs against the real answers, then runs the tests.
3. It uploads to the Direct Upload Pages project `prompt-guess` with `wrangler pages deploy`.

Repo secrets: `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`, `PUZZLES_DEPLOY_KEY` and `IMAGE_SALT`. The workflow only runs when the variable `DEPLOY_ENABLED` is `true`. The Pages project has the Workers AI binding `AI` (declared in `web/wrangler.toml`) and the same `IMAGE_SALT` as a secret.

To add new puzzles, push them to the private repo, then re-run Deploy (Actions → Deploy → Run workflow).

## Roadmap

- Streaks and stats, a "how scoring works" page and screenshots.
- Re-tune the scorer on real, anonymised guesses once there are some.
- Unlimited practice mode and an archive of past puzzles.
- Anonymous "most common wrong guess" stats.
- Optional custom domain.

Content rules: no adult content and no real people's faces.

## Licence

MIT
