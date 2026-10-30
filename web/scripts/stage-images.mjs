// Copy puzzle images into dist/i/ under salted, unguessable names (see functions/api/image.ts).
import { createHash } from "node:crypto";
import { mkdirSync, copyFileSync, readFileSync } from "node:fs";
const salt = process.env.IMAGE_SALT || "dev-only-salt";
if (!process.env.IMAGE_SALT) console.warn("stage-images: IMAGE_SALT not set, using the dev salt (fine locally, not for production)");
const puzzles = JSON.parse(readFileSync(new URL("../../puzzles/puzzles.json", import.meta.url)));
mkdirSync(new URL("../dist/i/", import.meta.url), { recursive: true });
for (const p of puzzles) {
  const name = createHash("sha256").update(`${salt}:${p.id}`).digest("hex").slice(0, 32);
  copyFileSync(new URL(`../../${p.image}`, import.meta.url), new URL(`../dist/i/${name}.webp`, import.meta.url));
}
console.log(`stage-images: ${puzzles.length} images`);
