// Client-side game state. The client never sees the answer until /api/reveal releases it.
export const MAX = 5;
export const WIN = 85;
export const EMOJI = { great: "🟩", close: "🟨", partial: "🟧", miss: "⬛" };
export const LABEL = { great: "Spot on", close: "Close", partial: "Warm", miss: "Cold" };
const KEY = "promptguess:v1";

export function load() {
  try { return JSON.parse(localStorage.getItem(KEY)) ?? { games: {} }; } catch { return { games: {} }; }
}
export function save(store) {
  try { localStorage.setItem(KEY, JSON.stringify(store)); } catch { /* private mode */ }
}

const prevDay = (d) => { const t = new Date(d + "T12:00:00Z"); t.setUTCDate(t.getUTCDate() - 1); return t.toISOString().slice(0, 10); };

/** Current streak: consecutive won days ending today (or yesterday, if today isn't finished). */
export function stats(store, today) {
  const games = Object.entries(store.games).filter(([, g]) => g.done);
  const won = games.filter(([, g]) => g.won).length;
  let d = store.games[today]?.done ? today : prevDay(today), streak = 0;
  while (store.games[d]?.won) { streak++; d = prevDay(d); }
  let best = 0, run = 0;
  for (const [, g] of games.sort(([a], [b]) => a.localeCompare(b))) { run = g.won ? run + 1 : 0; best = Math.max(best, run); }
  return { played: games.length, won, streak, best: Math.max(best, streak) };
}

export function shareText(number, game, url) {
  const n = game.won ? game.results.length : "X";
  const rows = game.results.map((r) => `${EMOJI[r.bucket]} ${Math.round(r.score)}`).join("\n");
  return `Prompt Guess #${number} ${n}/${MAX}\n${rows}\n${url}`;
}
