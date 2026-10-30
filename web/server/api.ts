// Server-only puzzle + scoring logic for the Pages Functions. Never imported by src/.
import puzzles from "../.puzzles/puzzles.json";
import synonymGroups from "../.puzzles/synonyms.json";
import { addSynonymGroups, cosine, scoreFromCosine, maskAnswer, PARAMS, type ScoreResult } from "./scoring.ts";

export interface Env {
  AI?: { run(model: string, input: { text: string[] }): Promise<{ data: number[][] }> };
  ASSETS: { fetch(req: Request | string): Promise<Response> };
  EMBED_URL?: string;   // local dev: python scoring/embed_server.py
  FAKE_TODAY?: string;  // local dev only: pretend today is this YYYY-MM-DD
  IMAGE_SALT?: string;  // must match the salt used by scripts/stage-images.mjs at build time
}
interface Puzzle { id: number; date: string; prompt: string; difficulty: string; image: string; alt: string }
const PUZZLES = puzzles as Puzzle[];
addSynonymGroups(synonymGroups as string[][]);
const MODEL = "@cf/baai/bge-small-en-v1.5";
export const MAX_GUESSES = 5;
export const MAX_GUESS_CHARS = 120;

export const json = (body: unknown, status = 200, extra: Record<string, string> = {}) =>
  new Response(JSON.stringify(body), { status, headers: { "content-type": "application/json", "cache-control": "no-store", ...extra } });

export function ukToday(env: Env, now = new Date()): string {
  if (env.FAKE_TODAY && /^\d{4}-\d{2}-\d{2}$/.test(env.FAKE_TODAY)) return env.FAKE_TODAY;
  return new Intl.DateTimeFormat("en-CA", { timeZone: "Europe/London", year: "numeric", month: "2-digit", day: "2-digit" }).format(now);
}

/** Only today's and past puzzles exist as far as the outside world is concerned. */
export function playable(env: Env, date: unknown): Puzzle | null {
  if (typeof date !== "string" || !/^\d{4}-\d{2}-\d{2}$/.test(date) || date > ukToday(env)) return null;
  return PUZZLES.find((p) => p.date === date) ?? null;
}
export const latest = (env: Env) => [...PUZZLES].reverse().find((p) => p.date <= ukToday(env)) ?? null;
export const firstDate = PUZZLES[0]?.date;

export const publicInfo = (p: Puzzle) => ({
  id: p.id, number: p.id, date: p.date, alt: p.alt, difficulty: p.difficulty,
  image: `/api/image?date=${p.date}`, maxGuesses: MAX_GUESSES,
  // Small words ("a", "on", "the") are shown from the start; content words are blanks.
  mask: maskAnswer(p.prompt, []).map((t) => (t.content ? null : t.word)),
});

// ---- embeddings -------------------------------------------------------------------------
const cache = new Map<string, number[]>();
async function embed(env: Env, texts: string[]): Promise<number[][]> {
  const need = texts.filter((t) => !cache.has(t));
  if (need.length) {
    let vecs: number[][];
    if (env.AI && !env.EMBED_URL) vecs = (await env.AI.run(MODEL, { text: need })).data;
    else if (env.EMBED_URL) {
      const r = await fetch(env.EMBED_URL, { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify({ texts: need }) });
      if (!r.ok) throw new Error(`embed server ${r.status}`);
      vecs = ((await r.json()) as { vectors: number[][] }).vectors;
    } else throw new Error("no embedding backend: bind Workers AI as AI, or set EMBED_URL");
    need.forEach((t, i) => cache.set(t, vecs[i]));
    if (cache.size > 2000) cache.clear();
  }
  return texts.map((t) => cache.get(t)!);
}

export async function scoreGuess(env: Env, p: Puzzle, guess: string): Promise<ScoreResult & { reveal: Record<number, string> }> {
  const [a, g] = await embed(env, [p.prompt, guess.trim()]);
  const r = scoreFromCosine(p.prompt, guess, cosine(a, g));
  const reveal: Record<number, string> = {};
  maskAnswer(p.prompt, r.matched).forEach((t, i) => { if (t.content && t.hit) reveal[i] = t.word; });
  return { ...r, reveal };
}
export const isWin = (r: ScoreResult) => r.score >= PARAMS.thresholds.great;

// ---- light rate limit (per isolate, best effort) ---------------------------------------------
const hits = new Map<string, number[]>();
export function rateLimited(req: Request, limit = 30, windowMs = 60_000): boolean {
  const ip = req.headers.get("cf-connecting-ip") ?? "local";
  const now = Date.now();
  const arr = (hits.get(ip) ?? []).filter((t) => now - t < windowMs);
  arr.push(now);
  hits.set(ip, arr);
  if (hits.size > 5000) hits.clear();
  return arr.length > limit;
}

// ---- images ----------------------------------------------------------------------------------
export async function imageName(salt: string, id: number): Promise<string> {
  const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(`${salt}:${id}`));
  return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("").slice(0, 32);
}
export const DEV_SALT = "dev-only-salt";
