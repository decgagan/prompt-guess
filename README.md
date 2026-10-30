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

**Milestone 2 (first 30 puzzles): done.** The 30 real puzzles (answers, images, image-model prompts and puzzle-specific synonym groups) live in the **private** repo `decgagan/prompt-guess-puzzles`, so the answers can't be read from GitHub. This repo has only [`puzzles-sample/`](puzzles-sample/): three fake puzzles in the same format, used by tests, CI and local dev when the private data isn't there.

> **Where puzzles come from:** `$PUZZLES_DIR`, else a `prompt-guess-puzzles` checkout next to this repo, else `puzzles-sample/`. Answers stay server-side: the client gets only the date, image and alt text, and the build fails if any answer ends up in the bundle.

**Milestone 3 (playable game): done.** [`web/`](web/) is a Svelte 5 + Vite app with Cloudflare Pages Functions in `web/functions/api/`:

- `GET /api/today`: today's puzzle by UK date (number, alt text, image URL, blanked prompt). No answer.
- `POST /api/guess {date, guess}`: score 0–100, bucket, matched words and their positions in the prompt. Only today's or past puzzles.
- `POST /api/reveal {date, guesses}`: the full prompt, only once the game is over (5 guesses, a winning last guess re-scored on the server, or a past puzzle).
- `GET /api/image?date=`: the image for a playable date. Images are built to unguessable hashed names (`IMAGE_SALT`), so future images can't be listed or fetched.
- Light per-IP rate limit (30 req/min, per isolate).

`web/server/scoring.ts` is a straight TypeScript port of scorer v3 (keyword lemmas, v2 synonyms, calibration from `params.json`). `npm test` checks it against Python-computed scores for all 76 eval + hand-rated pairs (they match to ±0.0, same bucket 76/76), and checks that no answer is in the built bundle (`npm run build` also fails if one is). The parity fixture uses only the public synonym tables. Puzzle synonym groups come from `synonyms.json` in the puzzle data and are merged in by both the Python and the TypeScript scorer.

> **Parity note:** the fixture uses the cosines from the local Python model. Live Workers AI embeddings for `bge-small-en-v1.5` may differ slightly (quantisation/runtime), so live scores can be a point or so away from the Python prototype.

### Run locally

```bash
# 0. (optional) the real puzzles, next to this repo; without them you get the fake sample
git clone https://github.com/decgagan/prompt-guess-puzzles ../prompt-guess-puzzles
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

Cloudflare Pages must **not** build from this repo on its own (it would only see the fake sample). Instead the [`Deploy`](.github/workflows/deploy.yml) GitHub Actions workflow checks out this repo and the private puzzles repo, builds with the real puzzles (the leak check runs against them) and uploads with `wrangler pages deploy`. It runs on every push to `main` once switched on.

What Dec needs to create (nothing has been created yet):

1. **Cloudflare Pages project** `prompt-guess` as a *Direct Upload* project (not connected to Git). Production branch `main`.
2. **Pages project settings:** the Workers AI binding `AI` (Settings → Functions → Bindings; also declared in `web/wrangler.toml` for production and preview), and the secret `IMAGE_SALT` (a long random string).
3. **Cloudflare API token** with *Account → Cloudflare Pages → Edit*, plus the account ID.
4. **Fine-grained GitHub token** with access to `decgagan/prompt-guess-puzzles` only, *Contents: Read-only*.
5. **GitHub secrets on this repo:** `CLOUDFLARE_API_TOKEN`, `CLOUDFLARE_ACCOUNT_ID`, `PUZZLES_REPO_TOKEN`, `IMAGE_SALT` (the **same** value as the Pages secret, because the build names images with it). Then set the repo **variable** `DEPLOY_ENABLED=true`.
6. Custom domain on the Pages project.

New puzzles: push them to the private repo, then re-run the Deploy workflow (Actions → Deploy → Run workflow).

## Plan

- **Front end:** Svelte + Vite on Cloudflare Pages.
- **Scoring:** a Cloudflare Worker using Workers AI `@cf/baai/bge-small-en-v1.5`, the same model as the Python prototype, so the calibration carries over.
- **Puzzles:** prompts and images generated ahead of time and checked by hand; answers stay server-side.
- **Progress:** streaks kept in the browser; no accounts.

## Milestones

1. ✅ **Scoring engine:** embeddings + calibrated 0–100 + keyword hits, with an eval set, metrics and tuning.
2. ✅ **First 30 puzzles:** prompts, images, quality and safety checks. Kept in the private puzzles repo; format in [`puzzles-sample/`](puzzles-sample/).
3. ✅ **Playable game:** guess input, score bar, keyword reveals, share grid.
4. **Launch:** domain, streaks, stats, "how scoring works" page, screenshots.
5. **Extras:** unlimited practice mode, archive, anonymous "most common wrong guess" stats.

Rules for content: no adult content, no real people's faces.

## Licence

MIT
