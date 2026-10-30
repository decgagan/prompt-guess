import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { scoreFromCosine } from "../server/scoring.ts";

const fx = JSON.parse(readFileSync(new URL("./parity_fixture.json", import.meta.url), "utf8"));

test("TS port matches the Python v3 scorer on eval + Dec's pairs (recorded cosines)", () => {
  let maxDiff = 0, sameBucket = 0;
  for (const r of fx) {
    const ts = scoreFromCosine(r.answer, r.guess, r.cosine);
    const d = Math.abs(ts.score - r.score);
    maxDiff = Math.max(maxDiff, d);
    assert.ok(d <= 1, `${r.answer} / ${r.guess}: ts=${ts.score} py=${r.score}`);
    assert.deepEqual(ts.matched, r.matched, `${r.answer} / ${r.guess}`);
    if (ts.bucket === r.bucket) sameBucket++;
  }
  console.log(`parity: ${fx.length} pairs, max |diff| = ${maxDiff.toFixed(2)}, same bucket ${sameBucket}/${fx.length}`);
  assert.equal(sameBucket, fx.length);
});
