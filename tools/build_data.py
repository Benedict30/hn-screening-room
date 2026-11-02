"""Compact the HackerTube data pack into the files the site loads.

Inputs (in DATA_DIR): videos.jsonl, taxonomy.json, and the derived copies of
mentions / related / embeddings in fc/. Output: SITE_DIR/data/.
"""
import glob
import json
import re
import shutil
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

DATA = Path(sys.argv[1])
OUT = Path(sys.argv[2]) / "data"
SHARDS = 48

CT = ["talk", "lecture", "course", "documentary", "explainer", "interview", "podcast",
      "tutorial", "demo", "news", "commentary", "comedy", "music", "other"]
LV = ["general", "intro", "intermediate", "advanced"]
SL = ["evergreen", "dated", "news"]
STANCE = ["strong_rec", "rec", "reference", "joke", "critical"]


def dump(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")


def norm(t):
    return re.sub(r"[^a-z0-9]+", " ", t.lower()).strip()


rows = [json.loads(line) for line in open(DATA / "videos.jsonl", encoding="utf-8")]
tax = json.load(open(DATA / "taxonomy.json", encoding="utf-8"))

# taxonomy: flat category list with area index
areas, cats, cat_index = [], [], {}
for ai, a in enumerate(tax["areas"]):
    areas.append({"id": a["id"], "name": a["name"]})
    for c in a["categories"]:
        cat_index[c["id"]] = len(cats)
        cats.append({"id": c["id"], "name": c["name"], "area": ai, "desc": c["description"]})

# merge duplicate uploads (same normalized title): keep the best-scored one
groups = defaultdict(list)
for r in rows:
    groups[norm(r["title"])].append(r)
alts, drop = {}, set()
for g in groups.values():
    if len(g) > 1:
        g.sort(key=lambda r: -r["score"])
        alts[g[0]["vid"]] = [x["vid"] for x in g[1:]]
        drop.update(x["vid"] for x in g[1:])
alias = {a: keep for keep, lst in alts.items() for a in lst}

rows = [r for r in rows if r["vid"] not in drop]
rows.sort(key=lambda r: (-r["score"], -r["hn"]["recommenders"], r["title"]))
idx = {r["vid"]: i for i, r in enumerate(rows)}

videos = []
for r in rows:
    h = r["hn"]
    q = r.get("quote") or {}
    videos.append([
        r["vid"], r["title"], r["channel"], r["summary"], r["why_hn"],
        CT.index(r["content_type"]), LV.index(r["level"]), SL.index(r["shelf_life"]),
        r["primary_topic"], "|".join(r["tags"]),
        [cat_index[c["id"]] for c in r["categories"] if c["id"] in cat_index],
        q.get("text") or "", q.get("hn_comment_id") or 0, int(q.get("year") or 0),
        h["recommenders"], h["rec_months"], h["strong_recs"], h["mentions"],
        h["first_year"], h["last_year"], r["score"], alts.get(r["vid"], []),
    ])

# comments, sharded by video index
by_video = defaultdict(list)
seen = set()
for f in glob.glob(str(DATA / "fc" / "comments" / "*.json")):
    for vid, cs in json.load(open(f, encoding="utf-8")).items():
        if not isinstance(cs, list):
            continue
        for c in cs:
            v = alias.get(c["vid"], c["vid"])
            key = (c["hnCommentId"], v)
            if v not in idx or key in seen:
                continue
            seen.add(key)
            by_video[idx[v]].append(c)
shards = [dict() for _ in range(SHARDS)]
n_comments = 0
for vi, cs in by_video.items():
    cs.sort(key=lambda c: (STANCE.index(c["stance"]), c["month"]))
    shards[vi % SHARDS][vi] = [[c["hnCommentId"], c["author"], c["month"], c["storyTitle"],
                                STANCE.index(c["stance"]), c["why"], c["quote"], c["text"]] for c in cs]
    n_comments += len(cs)

# embeddings: reorder to our index, similar videos, int8 copy for the For You feed
ids = json.load(open(DATA / "fc" / "embedding-ids.json"))
emb_all = np.load(DATA / "fc" / "embeddings.npy").astype(np.float32)
row_of = {v: i for i, v in enumerate(ids)}
emb = np.stack([emb_all[row_of[r["vid"]]] for r in rows])
emb /= np.linalg.norm(emb, axis=1, keepdims=True)
sims = emb @ emb.T
np.fill_diagonal(sims, -1)
similar = np.argsort(-sims, axis=1)[:, :16].tolist()
scale = 127.0 / float(np.abs(emb).max())

# shared-recommender graph
rel_src = json.load(open(DATA / "fc" / "related.json", encoding="utf-8"))
related = {}
for vid, lst in rel_src.items():
    v = alias.get(vid, vid)
    if v not in idx:
        continue
    out, got = [], set()
    for e in lst:
        t = alias.get(e["vid"], e["vid"])
        if t in idx and t != v and t not in got:
            got.add(t)
            out.append([idx[t], e["shared_recommenders"]])
    if out:
        related[idx[v]] = out[:16]

if OUT.exists():
    shutil.rmtree(OUT)
OUT.mkdir(parents=True)
import base64
(OUT / "emb.txt").write_text(base64.b64encode(np.clip(np.round(emb * scale), -127, 127).astype(np.int8).tobytes()).decode("ascii"))
dump(OUT / "catalog.json", {
    "exported": "2026-10-31",
    "fields": ["vid", "title", "channel", "summary", "why_hn", "content_type", "level",
               "shelf_life", "primary_topic", "tags", "categories", "quote", "quote_comment_id",
               "quote_year", "recommenders", "rec_months", "strong_recs", "mentions",
               "first_year", "last_year", "score", "alt_vids"],
    "content_types": CT, "levels": LV, "shelf_lives": SL, "stances": STANCE,
    "areas": areas, "categories": cats, "shards": SHARDS, "dims": 384,
    "videos": videos,
})
dump(OUT / "graph.json", {"similar": similar, "related": related})
for i, s in enumerate(shards):
    dump(OUT / "c" / f"{i:02d}.json", s)

total = sum(p.stat().st_size for p in OUT.rglob("*") if p.is_file())
print(f"videos {len(videos)} (merged {len(drop)} duplicate uploads), comments {n_comments}, "
      f"related {len(related)}, data {total/1e6:.1f} MB")
print("largest:", sorted(((p.stat().st_size, p.name) for p in OUT.rglob('*') if p.is_file()))[-4:])
