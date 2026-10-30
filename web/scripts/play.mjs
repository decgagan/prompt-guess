// Play a full game against a running `npm run pages:dev` (http://localhost:8788) on desktop and
// mobile, save screenshots, and fail on any console error. Usage: npm run play [-- outPrefix]
import { existsSync, readFileSync } from "node:fs";
import { chromium } from "playwright-core";

const URL_ = process.env.PLAY_URL ?? "http://localhost:8788/";
const OUT = process.argv[2] ?? "/workspace/prompt-guess";
const CHROME = [process.env.CHROME_PATH, "/usr/bin/google-chrome", "/usr/bin/google-chrome-stable", "/usr/bin/chromium",
  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"].filter(Boolean).find((p) => existsSync(p));
if (!CHROME) throw new Error("No Chrome/Chromium found. Set CHROME_PATH.");

// Desktop plays a near miss then wins with today's answer (read from web/.puzzles); mobile loses.
const today = await (await fetch(new URL("/api/today", URL_))).json();
const puzzle = JSON.parse(readFileSync(new URL("../.puzzles/puzzles.json", import.meta.url), "utf8")).find((p) => p.date === today.date);
if (!puzzle) throw new Error(`no local puzzle for ${today.date}`);
const words = puzzle.prompt.split(" ");
const runs = [
  { name: "desktop", viewport: { width: 1280, height: 900 }, guesses: ["something in a picture", words.slice(0, Math.ceil(words.length / 2)).join(" "), puzzle.prompt] },
  { name: "mobile", viewport: { width: 390, height: 844 }, mobile: true, guesses: ["a dog", "a cat in snow", "bird skiing", "a duck on a pond", "winter sports"] },
];
const errors = [];
const browser = await chromium.launch({ executablePath: CHROME, args: ["--no-sandbox"] });
try {
  for (const r of runs) {
    const ctx = await browser.newContext({ viewport: r.viewport, isMobile: !!r.mobile, hasTouch: !!r.mobile, deviceScaleFactor: r.mobile ? 2 : 1 });
    const page = await ctx.newPage();
    page.on("console", (m) => m.type() === "error" && errors.push(`${r.name}: ${m.text()}`));
    page.on("pageerror", (e) => errors.push(`${r.name}: ${e.message}`));
    await page.goto(URL_, { waitUntil: "networkidle" });
    await page.getByRole("dialog").waitFor();
    await page.screenshot({ path: `${OUT}-${r.name}-help.png` });
    await page.getByRole("button", { name: "Let's play" }).click();
    const input = page.locator("#guess");
    for (const [i, g] of r.guesses.entries()) {
      if (await page.locator(".result").count()) break;
      await input.fill(g);
      await input.press("Enter");
      await page.locator("ol.guesses li").nth(i).waitFor();
      await page.waitForFunction(() => !document.querySelector(".entry button")?.textContent?.includes("Scoring"));
      if (i === 1) await page.screenshot({ path: `${OUT}-${r.name}-mid.png`, fullPage: true });
    }
    await page.locator(".result").waitFor();
    await page.waitForTimeout(300);
    const share = await page.locator("pre.share").textContent();
    console.log(`${r.name}:\n${share}\n`);
    await page.screenshot({ path: `${OUT}-${r.name}-result.png`, fullPage: true });
    // Reload: state must persist.
    await page.reload({ waitUntil: "networkidle" });
    await page.locator(".result").waitFor();
    await ctx.close();
  }
} finally { await browser.close(); }
if (errors.length) { console.error("Console errors:\n" + errors.join("\n")); process.exit(1); }
console.log("play: both games completed, no console errors");
