import { json, playable, rateLimited, scoreGuess, isWin, ukToday, MAX_GUESSES, type Env } from "../../server/api.ts";

// The answer is released only once the game is over: a past puzzle, five guesses used,
// or a final guess that the server itself re-scores as a win.
export const onRequestPost: PagesFunction<Env> = async ({ request, env }) => {
  if (rateLimited(request)) return json({ error: "slow_down" }, 429, { "retry-after": "30" });
  let body: { date?: unknown; guesses?: unknown };
  try { body = await request.json(); } catch { return json({ error: "bad_json" }, 400); }
  const p = playable(env, body.date);
  if (!p) return json({ error: "no_such_puzzle" }, 404);
  const guesses = Array.isArray(body.guesses) ? body.guesses.filter((g): g is string => typeof g === "string" && !!g.trim()).slice(0, MAX_GUESSES) : [];
  let over = p.date < ukToday(env) || guesses.length >= MAX_GUESSES;
  if (!over && guesses.length) {
    try { over = isWin(await scoreGuess(env, p, guesses[guesses.length - 1])); } catch { return json({ error: "scoring_unavailable" }, 503); }
  }
  if (!over) return json({ error: "game_not_over" }, 403);
  return json({ prompt: p.prompt });
};
