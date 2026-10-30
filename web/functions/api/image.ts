import { playable, imageName, DEV_SALT, type Env } from "../../server/api.ts";

// Images are staged into dist/i/<sha256(salt:id)>.webp, so their URLs can't be guessed or listed;
// this endpoint releases one only on or after its puzzle date.
export const onRequestGet: PagesFunction<Env> = async ({ request, env }) => {
  const p = playable(env, new URL(request.url).searchParams.get("date"));
  if (!p) return new Response("Not found", { status: 404 });
  const name = await imageName(env.IMAGE_SALT || DEV_SALT, p.id);
  const r = await env.ASSETS.fetch(new URL(`/i/${name}.webp`, request.url).toString());
  if (!r.ok) return new Response("Not found", { status: 404 });
  return new Response(r.body, { headers: { "content-type": "image/webp", "cache-control": "public, max-age=86400" } });
};
