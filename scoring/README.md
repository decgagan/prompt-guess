# How the scoring works

A guess is scored by **what it means**, not whether it uses the exact words.

1. **Meaning (80%).** The guess and the real prompt are each turned into a list of 384 numbers (an *embedding*) by a small open model, [`BAAI/bge-small-en-v1.5`](https://huggingface.co/BAAI/bge-small-en-v1.5). Sentences that mean similar things get similar lists. We measure how alike they are with **cosine similarity**.
2. **Calibration.** Raw cosine values are awkward: with this model even unrelated sentences score around 0.4–0.5. So the cosine is stretched onto 0–100 with a fitted linear mapping: at or below **0.55** counts as 0, at or above **0.90** counts as 100.
3. **Key words (20%).** The prompt's content words (stopwords such as "a", "on", "the" removed) are reduced to a base form ("running" → "run", "puppies" → "puppy") and a small synonym table ("puppy" = "dog", "seaside" = "beach"). The share of them the guess hits is added in, and the matched words are returned so the game can reveal them.
4. **Buckets.** 85+ is **great**, 50+ **close**, 5+ **partial**, below that a **miss**.

## How it was tuned

`eval.csv` holds 64 hand-written pairs (16 prompts × 4 guesses, one per bucket). It is **synthetic test data**, written by us, not real player guesses. `evaluate.py --tune` grid-searches the cosine range, curve shape, keyword weight and bucket thresholds to maximise bucket accuracy plus Spearman correlation, while keeping exact paraphrases near 100 and unrelated guesses at 0.

| | Spearman | Bucket accuracy |
|---|---|---|
| Untuned defaults | 0.962 | 84.4% |
| Tuned | 0.968 | 95.3% |
| Tuned, 4-fold CV on unseen prompts | 0.969 | 92.2% |

Mean score by expected bucket: miss 0, partial 30, close 61, great 91.

## Why this model

`bge-small-en-v1.5` is small (33M parameters, runs on a laptop CPU) and is also hosted on Cloudflare Workers AI as `@cf/baai/bge-small-en-v1.5`, so the live game can use the same embeddings and the same calibration. The keyword step is rule-based (no downloads) so it can be ported straight to JavaScript.

## Limitations

- The eval set is small and written by one person; real guesses will be messier. Re-tune once real (anonymised) guesses exist.
- The synonym table is hand-made and short.
- Embeddings can't tell some opposites apart ("a happy dog" vs "a sad dog" score high).
