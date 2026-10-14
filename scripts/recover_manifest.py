"""Rebuild manifest attribution for already-downloaded files (no re-download).

For each <id>.jpg on disk missing from manifest.json, re-runs the same
search+keyword+license pipeline to recover the real file page URL, author
and license, then writes the entry back. Files whose source can no longer
be verified are KEPT ON DISK (status stays "pending") — never deleted,
never marked verified without proof.
"""

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.crop_image_queries import QUERIES  # noqa: E402
from scripts.crop_image_queries2 import QUERIES_CEREALS, QUERIES_FRUITS  # noqa: E402
from scripts.crop_image_queries3 import QUERIES_REST  # noqa: E402
from scripts.crop_image_queries4 import QUERIES_REST2  # noqa: E402
from scripts.fetch_crop_images import (  # noqa: E402
    OUT_DIR,
    MANIFEST,
    file_info,
    license_ok,
    search_files,
    title_ok,
)

all_q = QUERIES + QUERIES_FRUITS + QUERIES_CEREALS + QUERIES_REST + QUERIES_REST2
seen = {}
for cid, q, kw in all_q:
    seen.setdefault(cid, (q, kw))

manifest = {}
if MANIFEST.exists():
    try:
        manifest = {m["crop_id"]: m for m in json.loads(MANIFEST.read_text())}
    except Exception:
        manifest = {}

import urllib.parse

recovered, kept_pending, checked = 0, [], 0
for jpg in sorted(OUT_DIR.glob("*.jpg")):
    cid = jpg.stem
    if cid in manifest:
        continue
    if cid not in seen:
        # Crop not covered by this script's query tables: keep the file and
        # report it as pending rather than deleting it.
        kept_pending.append(cid)
        print(f"[{cid}] not covered by query tables — kept on disk, status pending")
        continue
    q, kw = seen[cid]
    # Retry the lookup a few times with backoff before giving up.
    lookup_ok = False
    for attempt in range(3):
        try:
            titles = search_files(q)
            pages = file_info(titles[:10])
        except Exception as exc:  # noqa: BLE001
            print(f"[{cid}] lookup failed (attempt {attempt + 1}/3): {type(exc).__name__}")
            if attempt < 2:
                time.sleep(5 * (attempt + 1))
            continue
        lookup_ok = True
        break
    if not lookup_ok:
        kept_pending.append(cid)
        print(f"[{cid}] lookup never succeeded — kept on disk, status pending")
        continue
    found = None
    for page in pages.values():
        title = page.get("title", "")
        infos = page.get("imageinfo") or []
        if not infos or not title_ok(title, kw):
            continue
        lic = license_ok(infos[0])
        if not lic:
            continue
        author = (infos[0].get("user") or "").strip()
        file_page = "https://commons.wikimedia.org/wiki/" + urllib.parse.quote(title.replace(" ", "_"))
        found = {
            "crop_id": cid,
            "file": f"images/crops/{cid}.jpg",
            "source_url": file_page,
            "source": "Wikimedia Commons",
            "author": author or "Unknown (see source page)",
            "license": lic,
            "verified": True,
            "bytes": jpg.stat().st_size,
        }
        break
    if found:
        manifest[cid] = found
        recovered += 1
        print(f"[{cid}] recovered: {found['license']} by {found['author']}")
    else:
        # Source genuinely unverifiable: keep the file on disk, do NOT delete.
        kept_pending.append(cid)
        print(f"[{cid}] source unverifiable — file kept on disk, status pending")
    checked += 1
    time.sleep(3)

MANIFEST.write_text(json.dumps([manifest[k] for k in sorted(manifest)], indent=1) + "\n")
print(f"\nRecovered: {recovered}, kept-on-disk-pending (unverifiable): {len(kept_pending)}, manifest total: {len(manifest)}")
if kept_pending:
    print("Pending-but-on-disk: " + ", ".join(sorted(kept_pending)))
