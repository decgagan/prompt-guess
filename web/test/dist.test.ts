import { test } from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { existsSync, mkdtempSync, readFileSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const script = new URL("../scripts/check-dist.mjs", import.meta.url).pathname;
const dist = new URL("../dist/", import.meta.url).pathname;
const run = (dir: string) => spawnSync(process.execPath, [script, dir], { encoding: "utf8" });
const puzzles = JSON.parse(readFileSync(new URL("../.puzzles/puzzles.json", import.meta.url), "utf8"));

test("built bundle contains no puzzle answers", { skip: !existsSync(dist) && "run npm run build first" }, () => {
  const r = run(dist);
  assert.equal(r.status, 0, r.stderr);
});

test("leak check catches a planted answer", () => {
  const dir = mkdtempSync(join(tmpdir(), "pg-dist-"));
  writeFileSync(join(dir, "ok.js"), "console.log('hello')");
  assert.equal(run(dir).status, 0);
  const words = puzzles[puzzles.length - 1].prompt.split(/\s+/);
  writeFileSync(join(dir, "leak.js"), `const x = ${JSON.stringify(words.slice(1, 5).join(" ").toUpperCase())};`);
  const r = run(dir);
  assert.equal(r.status, 1);
  assert.match(r.stderr, new RegExp(`#${puzzles[puzzles.length - 1].id}`));
});
