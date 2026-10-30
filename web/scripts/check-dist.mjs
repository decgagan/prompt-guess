// Uses web/.puzzles/ (the private puzzles when synced, else the sample).
// Fail the build if any puzzle answer (or a distinctive chunk of one) is in the client bundle.
import { readdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";
const puzzles = JSON.parse(readFileSync(new URL("../.puzzles/puzzles.json", import.meta.url)));
const dist = process.argv[2] ?? new URL("../dist/", import.meta.url).pathname;
const files = [];
const walk = (d) => { for (const n of readdirSync(d)) { const p = join(d, n); statSync(p).isDirectory() ? walk(p) : /\.(js|css|html|json|txt|map)$/.test(n) && files.push(p); } };
walk(dist);
const text = files.map((f) => readFileSync(f, "utf8").toLowerCase()).join("\n");
const leaks = [];
for (const p of puzzles) {
  const words = p.prompt.toLowerCase().split(/\s+/);
  const needles = [p.prompt.toLowerCase()];
  for (let i = 0; i + 4 <= words.length; i++) needles.push(words.slice(i, i + 4).join(" "));
  for (const n of needles) if (text.includes(n)) leaks.push(`#${p.id}: "${n}"`);
}
if (leaks.length) { console.error("check-dist: answers found in dist/:\n" + leaks.join("\n")); process.exit(1); }
console.log(`check-dist: ${files.length} files, no answers found`);
