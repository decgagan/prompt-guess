async function call(path, body) {
  const r = await fetch(path, body ? { method: "POST", headers: { "content-type": "application/json" }, body: JSON.stringify(body) } : {});
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw Object.assign(new Error(data.error || `HTTP ${r.status}`), { status: r.status, data });
  return data;
}
export const today = () => call("/api/today");
export const guess = (date, guess) => call("/api/guess", { date, guess });
export const reveal = (date, guesses) => call("/api/reveal", { date, guesses });
