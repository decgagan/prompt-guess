<script>
  import { onMount, tick } from "svelte";
  import * as api from "./lib/api.js";
  import { MAX, WIN, EMOJI, LABEL, load, save, stats, shareText } from "./lib/game.js";
  import Modal from "./lib/Modal.svelte";

  let puzzle = $state(null);
  let error = $state("");
  let store = $state({ games: {} });
  let input = $state("");
  let busy = $state(false);
  let notice = $state("");
  let showHelp = $state(false);
  let copied = $state(false);
  let inputEl;

  const game = $derived(puzzle ? store.games[puzzle.date] ?? { guesses: [], results: [], reveal: {}, done: false, won: false } : null);
  const st = $derived(puzzle ? stats(store, puzzle.today) : null);
  const words = $derived(puzzle ? puzzle.mask.map((w, i) => ({ word: w ?? game.reveal[i] ?? null, small: w !== null, i })) : []);
  const share = $derived(puzzle && game?.done ? shareText(puzzle.number, game, location.origin) : "");

  onMount(async () => {
    store = load();
    if (!localStorage.getItem("promptguess:seenHelp")) { showHelp = true; localStorage.setItem("promptguess:seenHelp", "1"); }
    try { puzzle = await api.today(); }
    catch (e) {
      error = e.data?.error === "no_puzzle_yet" ? `The first puzzle arrives on ${fmt(e.data.first)}.` : "Couldn't load today's puzzle. Please try again shortly.";
    }
  });

  function fmt(d) { return new Date(d + "T12:00:00Z").toLocaleDateString("en-GB", { weekday: "long", day: "numeric", month: "long", timeZone: "UTC" }); }

  function update(g) { store.games[puzzle.date] = g; save($state.snapshot(store)); }

  async function submit(e) {
    e.preventDefault();
    const text = input.replace(/\s+/g, " ").trim();
    if (!text || busy || game.done) return;
    if (game.guesses.some((g) => g.toLowerCase() === text.toLowerCase())) { notice = "You've already tried that one."; return; }
    busy = true; notice = "";
    try {
      const r = await api.guess(puzzle.date, text);
      const g = $state.snapshot(game);
      g.guesses.push(text);
      g.results.push({ score: r.score, bucket: r.bucket, matched: r.matched });
      Object.assign(g.reveal, r.reveal);
      g.won = r.score >= WIN;
      g.done = g.won || g.guesses.length >= MAX;
      input = "";
      notice = `Guess ${g.guesses.length}: ${Math.round(r.score)} out of 100, ${LABEL[r.bucket]}.` + (r.matched.length ? ` Matched: ${r.matched.join(", ")}.` : "");
      if (g.done) {
        const rv = await api.reveal(puzzle.date, g.guesses);
        g.prompt = rv.prompt;
        notice += g.won ? " You got it!" : ` The prompt was: ${rv.prompt}.`;
      }
      update(g);
    } catch (err) {
      notice = err.status === 429 ? "Easy there! Try again in a few seconds." : "That guess didn't go through. Please try again.";
    } finally {
      busy = false;
      await tick();
      if (!game.done) inputEl?.focus();
    }
  }

  async function copy() {
    try { await navigator.clipboard.writeText(share); copied = true; setTimeout(() => (copied = false), 2000); }
    catch { notice = "Couldn't copy. Select the text and copy it yourself."; }
  }
</script>

<header class="top">
  <h1><span class="logo" aria-hidden="true"><i></i><i></i><i></i></span>Prompt Guess</h1>
  <button class="icon" onclick={() => (showHelp = true)} aria-label="How to play">?</button>
</header>

<main>
  {#if error}
    <p class="card msg">{error}</p>
  {:else if !puzzle}
    <p class="card msg" aria-busy="true">Loading today's image…</p>
  {:else}
    <p class="meta">No. {puzzle.number} · {fmt(puzzle.date)}</p>
    <figure class="art">
      <img src={puzzle.image} alt={puzzle.alt} width="1024" height="1024" />
    </figure>

    <section aria-label="The prompt so far" class="prompt" class:solved={game.done}>
      {#if game.prompt}
        <p class="full"><span class="sr-only">The prompt was: </span>{game.prompt}</p>
      {:else}
        <p aria-label={words.map((w) => w.word ?? "blank").join(" ")}>
          {#each words as w (w.i)}
            {#if w.word}<span class={w.small ? "small" : "hit"} aria-hidden="true">{w.word}</span>
            {:else}<span class="blank" aria-hidden="true"></span>{/if}
          {/each}
        </p>
      {/if}
    </section>

    <ol class="guesses" aria-label="Your guesses">
      {#each Array(MAX) as _, i}
        {@const r = game.results[i]}
        <li class="row {r ? r.bucket : 'empty'}">
          {#if r}
            <span class="text">{game.guesses[i]}</span>
            <span class="bar" aria-hidden="true"><span style="width:{Math.max(r.score, 2)}%"></span></span>
            <span class="score"><span aria-hidden="true">{EMOJI[r.bucket]}</span> {Math.round(r.score)}<span class="sr-only"> out of 100, {LABEL[r.bucket]}</span></span>
          {:else}
            <span class="text muted">Guess {i + 1}</span>
          {/if}
        </li>
      {/each}
    </ol>

    {#if !game.done}
      <form onsubmit={submit} class="entry">
        <label for="guess" class="sr-only">Describe the image</label>
        <input id="guess" bind:this={inputEl} bind:value={input} maxlength="120" autocomplete="off" autocapitalize="off" spellcheck="true"
          placeholder="Describe the image…" disabled={busy} />
        <button type="submit" disabled={busy || !input.trim()}>{busy ? "Scoring…" : "Guess"}</button>
      </form>
    {:else}
      <section class="card result" aria-label="Result">
        <h2>{game.won ? `Solved in ${game.guesses.length}!` : "Out of guesses"}</h2>
        <pre class="share" aria-label="Share text">{share}</pre>
        <button onclick={copy}>{copied ? "Copied ✓" : "Copy result"}</button>
        <dl class="stats">
          <div><dt>Played</dt><dd>{st.played}</dd></div>
          <div><dt>Won</dt><dd>{st.played ? Math.round((100 * st.won) / st.played) : 0}%</dd></div>
          <div><dt>Streak</dt><dd>{st.streak}</dd></div>
          <div><dt>Best</dt><dd>{st.best}</dd></div>
        </dl>
        <p class="muted">A new image every day at midnight UK time.</p>
      </section>
    {/if}
    <p class="notice" role="status" aria-live="polite">{notice}</p>
  {/if}
</main>

<Modal open={showHelp} onclose={() => (showHelp = false)} title="How to play">
  <p>Everyone gets the same AI-generated image each day. Your job is to guess the <strong>prompt</strong> that made it.</p>
  <ul>
    <li>You have <strong>{MAX} guesses</strong>. Each one scores 0–100 for how close its <em>meaning</em> is, so you don't need the exact words.</li>
    <li>Words you hit appear in the prompt above the guesses.</li>
    <li>Score <strong>{WIN} or more</strong> to win.</li>
  </ul>
  <p class="legend"><span>🟩 Spot on</span><span>🟨 Close</span><span>🟧 Warm</span><span>⬛ Cold</span></p>
  <p class="muted">Results share as coloured squares only, with no spoilers.</p>
</Modal>
