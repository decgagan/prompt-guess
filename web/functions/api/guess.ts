import { json, playable, rateLimited, scoreGuess, MAX_GUESS_CHARS, type Env } from "../../server/api.ts";

export const onRequestPost: PagesFunction<Env> = async ({ request, env }) => {
  if (rateLimited(request)) return json({ error: "slow_down" }, 429, { "retry-after": "30" });
  let body: { date?: unknown; guess?: unknown };
  try { body = await request.json(); } catch { return json({ error: "bad_json" }, 400); }
  const p = playable(env, body.date);
  if (!p) return json({ error: "no_such_puzzle" }, 404);
  const guess = typeof body.guess === "string" ? body.guess.replace(/\s+/g, " ").trim() : "";
  if (!guess || guess.length > MAX_GUESS_CHARS) return json({ error: "bad_guess" }, 400);
  try {
    return json(await scoreGuess(env, p, guess));
  } catch (e) {
    console.error(e);
    return json({ error: "scoring_unavailable" }, 503);
  }
};
