// Copy the puzzle data into web/.puzzles/ (gitignored), which the functions and build read.
// Source: $PUZZLES_DIR, else a `prompt-guess-puzzles` checkout next to the repo (the private
// data), else the public fake sample in puzzles-sample/.
import { cpSync, existsSync, rmSync } from "node:fs";
import { resolve } from "node:path";
const web = new URL("..", import.meta.url).pathname;
const sibling = resolve(web, "../../prompt-guess-puzzles");
const src = process.env.PUZZLES_DIR ? resolve(process.env.PUZZLES_DIR)
  : existsSync(`${sibling}/puzzles.json`) ? sibling : resolve(web, "../puzzles-sample");
if (!existsSync(`${src}/puzzles.json`)) { console.error(`sync-puzzles: no puzzles.json in ${src}`); process.exit(1); }
const out = resolve(web, ".puzzles");
rmSync(out, { recursive: true, force: true });
for (const f of ["puzzles.json", "synonyms.json", "images"]) if (existsSync(`${src}/${f}`)) cpSync(`${src}/${f}`, `${out}/${f}`, { recursive: true });
if (!existsSync(`${out}/synonyms.json`)) cpSync(resolve(web, "../puzzles-sample/synonyms.json"), `${out}/synonyms.json`);
console.log(`sync-puzzles: ${src}${src.endsWith("puzzles-sample") ? " (FAKE SAMPLE)" : ""}`);
