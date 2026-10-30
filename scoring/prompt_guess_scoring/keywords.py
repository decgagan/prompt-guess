"""Keyword matching: lemmatised content-word overlap with light synonym tolerance.

Deliberately rule-based (no WordNet download) so it can be ported line-for-line
to the Cloudflare Worker in JavaScript.
"""
from __future__ import annotations

import re

STOPWORDS = frozenset("""
a an the and or but of in on at to for with by from into onto over under above below
up down out off near beside behind between through during while as is are was were be
been being am it its this that these those there here some any each every very
has have had do does did his her their our my your he she they we you i me him them
who whom which what when where why how all no not so than then too just can will
one ones image picture photo photograph showing shows scene view style render
""".split())

# Small, cheap synonym groups -> canonical form. Extend as puzzles demand.
_SYN_GROUPS = [
    ["dog", "puppy", "hound", "pup", "doggy"],
    ["cat", "kitten", "kitty", "feline"],
    ["car", "automobile", "vehicle", "auto"],
    ["sea", "ocean", "seaside", "beach", "shore", "coast"],
    ["big", "large", "huge", "giant", "enormous", "massive"],
    ["small", "tiny", "little", "miniature", "mini"],
    ["city", "town", "metropolis", "urban"],
    ["forest", "wood", "woods", "woodland", "jungle"],
    ["mountain", "mount", "peak", "hill"],
    ["boat", "ship", "sailboat", "yacht", "vessel"],
    ["robot", "android", "droid", "machine"],
    ["night", "nighttime", "midnight", "evening"],
    ["sunset", "dusk", "twilight", "sundown"],
    ["house", "home", "cottage", "cabin"],
    ["astronaut", "spaceman", "cosmonaut"],
    ["happy", "joyful", "cheerful", "smiling"],
    ["sad", "unhappy", "crying", "gloomy"],
    ["old", "ancient", "elderly", "aged", "vintage"],
    ["painting", "painted", "oil", "watercolour", "watercolor"],
    ["rain", "rainy", "raining", "storm", "stormy"],
    ["snow", "snowy", "snowing", "winter"],
    ["fox", "vixen"],
    ["bird", "parrot", "sparrow", "pigeon"],
    ["kid", "child", "boy", "girl", "children"],
    ["man", "guy", "gentleman"],
    ["woman", "lady"],
    ["eat", "eating", "eats", "ate", "munching"],
    ["read", "reading", "reads"],
    ["fly", "flying", "flies", "soaring", "floating"],
    ["run", "running", "runs", "sprinting", "jogging"],
    ["coffee", "espresso", "latte", "cappuccino"],
    ["tea", "teacup"],
    ["castle", "fortress", "palace"],
    ["dragon", "wyvern"],
    ["space", "galaxy", "cosmos", "outer"],
    ["street", "road", "alley", "avenue"],
    ["neon", "glowing", "cyberpunk"],
]
# v2 additions: broader / near-synonym words players reach for.
_SYN_GROUPS_V2 = [
    ["horse", "horseback", "pony", "stallion", "steed"],
    ["chess", "game", "boardgame"],
    ["park", "outside", "outdoors", "outdoor"],
    ["robot", "machine", "android", "droid", "bot", "cyborg"],
    ["astronaut", "spaceman", "cosmonaut", "spacewoman"],
    ["ride", "riding", "rides", "rode", "riding"],
    ["balloon", "airship", "blimp"],
    ["cabin", "house", "home", "cottage", "hut", "lodge"],
    ["arctic", "ice", "icy", "polar", "glacier"],
    ["drink", "drinking", "sipping", "sip", "drinks"],
    ["water", "watering", "watered"],
    ["plant", "plants", "flower", "flowers"],
]
SYNONYMS = {w: g[0] for g in _SYN_GROUPS for w in g}
SYNONYMS_V2 = dict(SYNONYMS)
for _g in _SYN_GROUPS_V2:
    _c = SYNONYMS_V2.get(_g[0], _g[0])
    for _w in _g:
        SYNONYMS_V2[_w] = _c

_IRREGULAR = {"mice": "mouse", "geese": "goose", "feet": "foot", "teeth": "tooth",
              "men": "man", "women": "woman", "children": "child", "people": "person",
              "wolves": "wolf", "leaves": "leaf", "knives": "knife", "ate": "eat"}


def lemma(word: str) -> str:
    w = word.lower()
    if w in _IRREGULAR:
        return _IRREGULAR[w]
    if w in SYNONYMS:
        return w
    for suf, rep in (("ies", "y"), ("ves", "f"), ("sses", "ss"), ("ches", "ch"), ("shes", "sh"), ("xes", "x")):
        if w.endswith(suf) and len(w) > len(suf) + 2:
            return w[: -len(suf)] + rep
    if w.endswith("ing") and len(w) > 5:
        base = w[:-3]
        if len(base) > 2 and base[-1] == base[-2]:
            base = base[:-1]
        return base
    if w.endswith("ed") and len(w) > 4:
        return w[:-2]
    if w.endswith("s") and not w.endswith(("ss", "us", "is")) and len(w) > 3:
        return w[:-1]
    return w


def canonical(word: str, syn: dict | None = None) -> str:
    syn = SYNONYMS if syn is None else syn
    w = word.lower()
    if w in syn:
        return syn[w]
    l = lemma(w)
    return syn.get(l, l)


def content_words(text: str) -> list[str]:
    toks = re.findall(r"[a-z]+", text.lower())
    return [t for t in toks if t not in STOPWORDS and len(t) > 1]


def keyword_match(answer: str, guess: str, version: int = 1) -> tuple[float, list[str]]:
    """Return (recall of the answer's content words, matched answer words)."""
    ans = content_words(answer)
    if not ans:
        return 0.0, []
    syn = SYNONYMS_V2 if version >= 2 else SYNONYMS
    guess_canon = {canonical(t, syn) for t in content_words(guess)}
    matched, seen = [], set()
    for t in ans:
        c = canonical(t, syn)
        if c in seen:
            continue
        seen.add(c)
        if c in guess_canon:
            matched.append(t)
    return len(matched) / len(seen), matched
