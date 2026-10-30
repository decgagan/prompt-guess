<script>
  let { open, onclose, title, children } = $props();
  let dlg;
  $effect(() => { if (!dlg) return; if (open && !dlg.open) dlg.showModal(); else if (!open && dlg.open) dlg.close(); });
</script>

<dialog bind:this={dlg} onclose={onclose} aria-labelledby="dlg-title" onclick={(e) => e.target === dlg && onclose()}>
  <div class="dlg">
    <header><h2 id="dlg-title">{title}</h2><button class="icon" onclick={onclose} aria-label="Close">✕</button></header>
    {@render children()}
    <button class="wide" onclick={onclose}>Let's play</button>
  </div>
</dialog>
