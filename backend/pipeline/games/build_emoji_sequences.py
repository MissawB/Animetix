"""Offline precompute for the CPU-only "Emoji" game.

For every anime / manga / character we turn the most important words of its
title, description, genres and tags into a short sequence of emojis using a
local CPU sentence-embedding model (all-MiniLM-L6-v2) — NO GPU, NO LLM. Each
important word is embedded and matched (cosine) to the closest emoji in a
curated lexicon; the resulting emojis are ordered from the VAGUEST (generic,
e.g. a genre) to the most OBVIOUS (a specific, rare, on-the-nose hint) so the
game can reveal them one at a time, easier with every failed guess.

Output: ``data/artifacts/emoji_sequences.json`` = {media_type: {id: [emoji,...]}}.
Run once (offline):  python backend/pipeline/games/build_emoji_sequences.py
"""

import ast
import json
import re
from pathlib import Path

from sentence_transformers import SentenceTransformer

BASE_DIR = Path(__file__).resolve().parents[3]
PROCESSED = BASE_DIR / "data" / "processed"
ARTIFACTS = BASE_DIR / "data" / "artifacts"
LEXICON = PROCESSED / "emoji_lexicon.json"
OUT = ARTIFACTS / "emoji_sequences.json"

SOURCES = {
    "Anime": PROCESSED / "clean_root_animes.json",
    "Manga": PROCESSED / "clean_root_mangas.json",
    "Character": PROCESSED / "filtered_characters.json",
}
SEQ_LEN = 6  # emojis kept per title
SIM_THRESHOLD = 0.30  # ignore weak keyword→emoji matches
MAX_ITEMS = 1500  # only the selectable popularity range (select_secret uses top 500)

_STOP = set(
    "the a an of and or to in on at is are was were be been being it its this that "
    "with for from as by he she they his her their who what when where which while "
    "into out up down over under after before between not no but his story world life "
    "one two her him them you your our their has have had will would can could".split()
)


def _as_list(value):
    if isinstance(value, list):
        return value
    if isinstance(value, str) and value.strip():
        try:
            parsed = ast.literal_eval(value)
            return parsed if isinstance(parsed, list) else [parsed]
        except (ValueError, SyntaxError):
            return [value]
    return []


def _desc_keywords(text, limit=12):
    words = re.findall(r"[A-Za-z][A-Za-z'-]{3,}", str(text or ""))
    seen, out = set(), []
    for w in words:
        lw = w.lower()
        if lw in _STOP or lw in seen:
            continue
        seen.add(lw)
        out.append(lw)
        if len(out) >= limit:
            break
    return out


def _item_keywords(item):
    """Return [(keyword, tier)] — tier 0 = vaguest (genre) … 2 = most specific."""
    kws = []
    for g in _as_list(item.get("genres")):
        kws.append((str(g), 0))
    for t in _as_list(item.get("tags"))[:12] + _as_list(item.get("micro_tags"))[:8]:
        kws.append((str(t), 1))
    for t in _as_list(item.get("traits"))[:8]:  # characters
        kws.append((str(t), 1))
    desc = (
        item.get("description")
        or item.get("clean_description")
        or item.get("biography")
    )
    for w in _desc_keywords(desc):
        kws.append((w, 2))
    return kws


def main():
    lexicon = json.loads(LEXICON.read_text(encoding="utf-8"))
    emojis = list(lexicon.keys())
    print(f"Loading model + embedding {len(emojis)} emojis…")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    emoji_vecs = model.encode(
        [lexicon[e] for e in emojis], normalize_embeddings=True, batch_size=64
    )

    result = {}
    for media_type, path in SOURCES.items():
        if not path.exists():
            print(f"  skip {media_type}: {path} missing")
            continue
        db = json.loads(path.read_text(encoding="utf-8"))[:MAX_ITEMS]
        print(f"{media_type}: {len(db)} items")

        # Embed every unique keyword once, then map keyword -> (emoji, similarity).
        item_kws = {str(it.get("id")): _item_keywords(it) for it in db}
        vocab = sorted({kw for kws in item_kws.values() for kw, _ in kws})
        kv = model.encode(vocab, normalize_embeddings=True, batch_size=128)
        sims = kv @ emoji_vecs.T  # (vocab, emojis) cosine (both normalized)
        best_idx = sims.argmax(axis=1)
        kw_map = {
            w: (emojis[best_idx[i]], float(sims[i, best_idx[i]]))
            for i, w in enumerate(vocab)
        }

        # Pass 1: pick the best (relevant) emojis per item.
        picks = {}
        freq = {}
        for it in db:
            iid = str(it.get("id"))
            best = {}  # emoji -> (sim, tier)
            for kw, tier in item_kws[iid]:
                emo, sim = kw_map.get(kw, (None, 0.0))
                if not emo or sim < SIM_THRESHOLD:
                    continue
                cur = best.get(emo)
                if cur is None or sim > cur[0]:
                    best[emo] = (sim, min(tier, cur[1]) if cur else tier)
            top = sorted(best.items(), key=lambda kv2: -kv2[1][0])[:SEQ_LEN]
            picks[iid] = top
            for emo, _ in top:
                freq[emo] = freq.get(emo, 0) + 1

        # Pass 2: order each item's emojis vague → obvious.
        maxf = max(freq.values()) if freq else 1
        seqs = {}
        for iid, top in picks.items():
            if not top:
                continue

            def obviousness(entry):
                emo, (sim, tier) = entry
                rarity = 1.0 - freq.get(emo, 1) / maxf
                return 0.5 * (tier / 2.0) + 0.3 * rarity + 0.2 * sim

            ordered = sorted(top, key=obviousness)  # vaguest first
            seqs[iid] = [emo for emo, _ in ordered]
        result[media_type] = seqs
        print(f"  built sequences for {len(seqs)}/{len(db)} items")

    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
