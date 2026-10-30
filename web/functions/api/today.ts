import { json, latest, publicInfo, ukToday, firstDate, type Env } from "../../server/api.ts";

export const onRequestGet: PagesFunction<Env> = ({ env }) => {
  const p = latest(env);
  if (!p) return json({ error: "no_puzzle_yet", today: ukToday(env), first: firstDate }, 404);
  return json({ ...publicInfo(p), today: ukToday(env) });
};
