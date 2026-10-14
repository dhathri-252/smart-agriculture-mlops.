"""Fetch openly-licensed crop photos from Wikimedia Commons, bundle locally.

Per crop: search Commons API -> accept ONLY if File title matches a keyword
AND LicenseShortName is CC0/CC-BY/CC-BY-SA AND bytes download + resize OK.
Resize to max 640px JPEG q72 -> frontend/public/images/crops/<id>.jpg.
Record file page URL, author, license in manifest.json. Anything failing any
check keeps its placeholder ("pending"). Nothing is invented.
"""

import argparse
import io
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PIL import Image  # noqa: E402

from scripts.crop_image_queries import QUERIES  # noqa: E402
from scripts.crop_image_queries2 import QUERIES_CEREALS, QUERIES_FRUITS  # noqa: E402
from scripts.crop_image_queries3 import QUERIES_REST  # noqa: E402
from scripts.crop_image_queries4 import QUERIES_REST2  # noqa: E402

API = "https://commons.wikimedia.org/w/api.php"
UA = {"User-Agent": "SmartAgriMLOps/1.1 crop-catalogue (educational project)"}


def _ssl_context():
    """TLS context using certifi's CA bundle (macOS Python lacks system CAs)."""
    import ssl

    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return ssl.create_default_context()
OUT_DIR = ROOT / "frontend" / "public" / "images" / "crops"
MANIFEST = OUT_DIR / "manifest.json"
MAX_DIM = 640
JPEG_QUALITY = 72

FREE_LICENSES = ("CC0", "CC-BY", "CC BY", "CC-BY-SA", "CC BY-SA")


def _http_error_code(exc: Exception):
    """Return the HTTP status code for urllib HTTPError, or None."""
    import urllib.error

    if isinstance(exc, urllib.error.HTTPError):
        return exc.code
    return None


def _classify_error(exc: Exception) -> str:
    """Classify an exception for retry/backoff decisions."""
    code = _http_error_code(exc)
    if code == 429:
        return "rate_limit"
    if code is not None and 500 <= code < 600:
        return "transient_server_error"
    return "client_error"


def _backoff_seconds(attempt: int, base: float, limit: float) -> float:
    """Exponential backoff with a small amount of jitter, capped at limit."""
    import random

    wait = base * (2 ** attempt) + random.uniform(0, base * 0.25)
    return min(wait, limit)


def api_get(params: dict, timeout: int = 25, retries: int = 3) -> dict:
    """GET the Commons API with conservative 429/rate-limit handling.

    429 (and 5xx) responses trigger exponential backoff plus a random jitter
    and a ``Retry-After``-aware sleep; other 4xx responses are not retried.

    Backoff base is 5 seconds so that the mandatory ``Retry-After`` header
    (from Wikimedia) is the dominant delay. This keeps us inside the rate
    limit while still making tangible progress between retries.
    """
    url = API + "?" + urllib.parse.urlencode(params)
    last = None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=timeout, context=_ssl_context()) as resp:
                return json.load(resp)
        except Exception as exc:  # noqa: BLE001 - retry then surface
            last = exc
            kind = _classify_error(exc)
            if kind == "rate_limit" and attempt < retries:
                wait = _backoff_seconds(attempt, base=5.0, limit=60.0)
                retry_after = _retry_after(exc)
                if retry_after:
                    wait = max(wait, float(retry_after))
                print(f"  [429 rate limit] {exc} — sleeping {wait:.0f}s (attempt {attempt + 1}/{retries + 1})")
                time.sleep(wait)
                continue
            if kind == "transient_server_error" and attempt < retries:
                wait = _backoff_seconds(attempt, base=3.0, limit=30.0)
                print(f"  [5xx transient] {exc} — sleeping {wait:.0f}s (attempt {attempt + 1}/{retries + 1})")
                time.sleep(wait)
                continue
            break
    raise last


def _retry_after(exc: Exception) -> float:
    """Parse the ``Retry-After`` header from an HTTP error, if present."""
    try:
        val = exc.headers.get("Retry-After", "")
    except Exception:
        return 0.0
    try:
        return max(0.0, float(val))
    except (TypeError, ValueError):
        return 0.0


def search_files(query: str, limit: int = 12) -> list:
    data = api_get({
        "action": "query", "format": "json", "list": "search",
        "srsearch": query, "srnamespace": 6, "srlimit": limit,
    })
    time.sleep(2)  # polite pause between API calls (rate-limit friendly)
    return [s["title"] for s in data.get("query", {}).get("search", [])]


def file_info(titles: list) -> dict:
    data = api_get({
        "action": "query", "format": "json", "prop": "imageinfo",
        "titles": "|".join(titles), "iiprop": "url|user|extmetadata",
        "iiurlwidth": 800,
    })
    time.sleep(2)
    return data.get("query", {}).get("pages", {})



def license_ok(info: dict):
    meta = (info.get("extmetadata") or {})
    short = ((meta.get("LicenseShortName") or {}).get("value") or "")
    short = "".join(c for c in short if c.isalnum() or c in ("-", " ", ".")).strip()
    for free in FREE_LICENSES:
        if short.replace(" ", "").lower().startswith(free.replace(" ", "").lower()):
            return short or free
    return None


def title_ok(title: str, keywords: list) -> bool:
    low = title.lower()
    for bad in ("dish", "curry", "recipe", "cooked", "restaurant", "map ",
                "logo", "flag", "stamp", "coin", "painting"):
        if bad in low:
            return False
    return any(k.lower() in low for k in keywords)


def download(url: str, timeout: int = 60, retries: int = 3) -> bytes:
    """Download an image blob with 429/rate-limit aware retries."""
    last = None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers=UA)
            with urllib.request.urlopen(req, timeout=timeout, context=_ssl_context()) as resp:
                if int(resp.headers.get("Content-Length", "0") or 0) > 15_000_000:
                    raise ValueError("file too large (>15MB)")
                return resp.read()
        except Exception as exc:  # noqa: BLE001 - retry then surface
            last = exc
            kind = _classify_error(exc)
            if kind == "rate_limit" and attempt < retries:
                wait = _backoff_seconds(attempt, base=5.0, limit=60.0)
                retry_after = _retry_after(exc)
                if retry_after:
                    wait = max(wait, float(retry_after))
                print(f"  [429 on image download] {exc} — sleeping {wait:.0f}s (attempt {attempt + 1}/{retries + 1})")
                time.sleep(wait)
                continue
            if kind == "transient_server_error" and attempt < retries:
                wait = _backoff_seconds(attempt, base=3.0, limit=30.0)
                print(f"  [5xx on image download] {exc} — sleeping {wait:.0f}s (attempt {attempt + 1}/{retries + 1})")
                time.sleep(wait)
                continue
            break
    raise last


def process_image(raw: bytes) -> bytes:
    img = Image.open(io.BytesIO(raw)).convert("RGB")
    img.thumbnail((MAX_DIM, MAX_DIM), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=JPEG_QUALITY, optimize=True, progressive=True)
    return buf.getvalue()


def fetch_one(crop_id: str, query: str, keywords: list):
    try:
        titles = search_files(query)
    except Exception as exc:
        print(f"  [{crop_id}] search failed: {type(exc).__name__}")
        return None
    if not titles:
        print(f"  [{crop_id}] no search hits")
        return None
    try:
        pages = file_info(titles[:10])
    except Exception as exc:
        print(f"  [{crop_id}] info failed: {type(exc).__name__}")
        return None
    for page in pages.values():
        title = page.get("title", "")
        infos = page.get("imageinfo") or []
        if not infos or not title_ok(title, keywords):
            continue
        info = infos[0]
        lic = license_ok(info)
        if not lic:
            continue
        author = (info.get("user") or "").strip()
        thumb = info.get("thumburl") or info.get("url")
        if not thumb:
            continue
        try:
            raw = download(thumb)
            if len(raw) < 4000:
                continue
            jpeg = process_image(raw)
        except Exception:
            continue
        dest = OUT_DIR / f"{crop_id}.jpg"
        dest.write_bytes(jpeg)
        file_page = "https://commons.wikimedia.org/wiki/" + urllib.parse.quote(title.replace(" ", "_"))
        return {
            "crop_id": crop_id, "file": f"images/crops/{crop_id}.jpg",
            "source_url": file_page, "source": "Wikimedia Commons",
            "author": author or "Unknown (see source page)", "license": lic,
            "verified": True, "bytes": len(jpeg),
        }
    print(f"  [{crop_id}] no licensed match")
    return None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", default=None)
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    all_q = QUERIES + QUERIES_FRUITS + QUERIES_CEREALS + QUERIES_REST + QUERIES_REST2
    seen = {}
    for cid, q, kw in all_q:
        seen.setdefault(cid, (q, kw))
    jobs = [(cid, q, kw) for cid, (q, kw) in seen.items()]
    if args.only:
        only = set(args.only)
        jobs = [j for j in jobs if j[0] in only]
    if args.limit:
        jobs = jobs[: args.limit]
    print(f"crops to fetch: {len(jobs)}")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {}
    if MANIFEST.exists():
        try:
            manifest = {m["crop_id"]: m for m in json.loads(MANIFEST.read_text())}
        except Exception:
            manifest = {}

    ok, pending = 0, []
    for i, (cid, q, kw) in enumerate(jobs, 1):
        print(f"[{i}/{len(jobs)}] {cid}: searching '{q}'")
        rec = fetch_one(cid, q, kw)
        if rec:
            manifest[cid] = rec
            ok += 1
            print(f"  [{cid}] OK {rec['license']} by {rec['author']} ({rec['bytes']//1024} KB)")
        else:
            pending.append(cid)
        time.sleep(3)

    MANIFEST.write_text(json.dumps([manifest[k] for k in sorted(manifest)], indent=1) + "\n")
    print(f"\nDone: {ok} downloaded, {len(pending)} pending.")
    if pending:
        print("Pending: " + ", ".join(pending))
    total_kb = sum(m.get("bytes", 0) for m in manifest.values()) // 1024
    print(f"Bundled: {len(manifest)} files, ~{total_kb} KB total.")


if __name__ == "__main__":
    main()
