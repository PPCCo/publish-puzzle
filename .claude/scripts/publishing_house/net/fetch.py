"""Quarantined research fetcher — the ONLY module permitted to touch the network.

Rule-18 carve-out (see ``.claude/rules/18-python.md``). Hard constraints, enforced
here so no caller can bypass them:

* **GET-only.** No POST/PUT/PATCH/DELETE, no request bodies, no auth headers.
* **Host-allowlisted.** A URL may be fetched only if its host is listed in
  ``.claude/config/research-sources.json`` (``sources[].host`` or ``search.host``).
* **No credentials.** Never reads ``.env``/secrets, never sends cookies or auth.
  Login-gated data is handled by a human "assisted" tier elsewhere, never here.
* **Cached.** Responses are cached under ``.publishing/cache/`` (gitignored).
* **Bounded.** Per-request timeout + capped exponential backoff; capped body size.
* **Explicitly enabled.** Network only happens when ``RESEARCH_FETCH_ENABLED=1``
  (or ``--allow-net`` via the CLI), otherwise every call returns a disabled stub.
* **Deterministic edge.** This is the one place clock/entropy/subprocess live. It
  MUST NOT import ``publishing_house`` core modules (state, gates, generators,
  verifiers, design-policy, builders); stdlib only.

Tiers implemented: ``search`` + ``get`` are Tier 2 (HTTP via urllib). ``render`` is
Tier 3 (headless browser via a Node/Playwright helper, invoked as an argument
array — never ``shell=True``); it degrades to a ``browser-unavailable`` signal when
no browser/helper is present.
"""
from __future__ import annotations

import hashlib
import html
import json
import os
import re
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# --- constants -------------------------------------------------------------

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0 Safari/537.36"
)
DEFAULT_TIMEOUT = 15  # seconds per attempt
MAX_ATTEMPTS = 3
MAX_BODY_BYTES = 4 * 1024 * 1024  # 4 MiB cap
CACHE_TTL_SECONDS = 24 * 60 * 60  # cache freshness window (Tier 0)
ENABLE_FLAG = "RESEARCH_FETCH_ENABLED"

_SEARCH_ENGINES = {
    "ddg": "https://html.duckduckgo.com/html/?q={q}",
}


class FetchError(ValueError):
    """Raised for disallowed operations (non-GET, non-allowlisted host, bad engine).

    Subclasses ``ValueError`` so the CLI's existing handler renders it as a clean
    ``{"status": "error", ...}`` (exit 2) without the quarantined module needing to
    import any core ``publishing_house`` module.
    """


# --- helpers ---------------------------------------------------------------


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _repo_root(start: Path | None = None) -> Path:
    configured = os.environ.get("PUBLISHING_REPO_ROOT")
    if configured:
        root = Path(configured).expanduser().resolve()
        if (root / ".claude").is_dir():
            return root
    current = Path(start or os.getcwd()).expanduser().resolve()
    for candidate in [current, *current.parents]:
        if (candidate / ".claude" / "CLAUDE.md").is_file():
            return candidate
    raise FetchError("Could not locate repository root containing .claude/CLAUDE.md")


def _sources_config(root: Path) -> dict[str, Any]:
    path = root / ".claude" / "config" / "research-sources.json"
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def allowed_hosts(root: Path) -> set[str]:
    """Every host the fetcher may contact: search host + each source host."""
    cfg = _sources_config(root)
    hosts: set[str] = set()
    search_host = cfg.get("search", {}).get("host")
    if search_host:
        hosts.add(search_host.lower())
    for source in cfg.get("sources", []):
        host = source.get("host")
        if host:
            hosts.add(host.lower())
    return hosts


def _host_of(url: str) -> str:
    return (urllib.parse.urlsplit(url).hostname or "").lower()


def _enabled() -> bool:
    return os.environ.get(ENABLE_FLAG) == "1"


def _cache_dir(root: Path) -> Path:
    d = root / ".publishing" / "cache" / "research-fetch"
    d.mkdir(parents=True, exist_ok=True)
    return d


def _cache_path(root: Path, url: str) -> Path:
    key = hashlib.sha256(url.encode("utf-8")).hexdigest()
    return _cache_dir(root) / f"{key}.json"


def _read_cache(root: Path, url: str) -> dict[str, Any] | None:
    path = _cache_path(root, url)
    if not path.is_file():
        return None
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    fetched_at = record.get("_fetched_epoch", 0)
    if time.time() - fetched_at > CACHE_TTL_SECONDS:
        return None
    return record


def _write_cache(root: Path, url: str, record: dict[str, Any]) -> Path:
    path = _cache_path(root, url)
    # Preserve an explicit _fetched_epoch (freshness anchor) if the caller set one;
    # otherwise stamp the write time. Never silently reset a provided timestamp.
    if "_fetched_epoch" not in record:
        record = {**record, "_fetched_epoch": time.time()}
    path.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


# --- Tier 2: HTTP GET ------------------------------------------------------


def _http_get(url: str, timeout: int = DEFAULT_TIMEOUT) -> dict[str, Any]:
    """Single GET with capped exponential backoff. No auth, no cookies, GET only."""
    last_error: str | None = None
    for attempt in range(MAX_ATTEMPTS):
        request = urllib.request.Request(
            url,
            method="GET",
            headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"},
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 (host allowlisted, GET-only)
                raw = response.read(MAX_BODY_BYTES + 1)
                truncated = len(raw) > MAX_BODY_BYTES
                body = raw[:MAX_BODY_BYTES].decode("utf-8", errors="replace")
                return {
                    "status": getattr(response, "status", 200),
                    "final_url": response.geturl(),
                    "body": body,
                    "truncated": truncated,
                }
        except urllib.error.HTTPError as exc:  # 4xx/5xx — do not retry client errors
            if exc.code in (429,) or 500 <= exc.code < 600:
                last_error = f"HTTP {exc.code}"
                time.sleep(min(2 ** attempt, 4))
                continue
            return {"status": exc.code, "final_url": url, "body": "", "truncated": False, "error": f"HTTP {exc.code}"}
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_error = str(exc)
            time.sleep(min(2 ** attempt, 4))
    return {"status": 0, "final_url": url, "body": "", "truncated": False, "error": last_error or "unreachable"}


def get(url: str, *, root: Path | None = None, use_cache: bool = True) -> dict[str, Any]:
    """GET an allowlisted URL. Returns a JSON-serialisable record; never raises for
    network failure (only for policy violations)."""
    root = root or _repo_root()
    host = _host_of(url)
    if not url.lower().startswith(("http://", "https://")):
        raise FetchError(f"Only http(s) URLs are permitted: {url}")
    if host not in allowed_hosts(root):
        raise FetchError(f"Host not in research-sources allowlist: {host!r}")

    if use_cache:
        cached = _read_cache(root, url)
        if cached is not None:
            return {**{k: v for k, v in cached.items() if not k.startswith("_")}, "from_cache": True, "tier": "cache"}

    if not _enabled():
        return {
            "status": 0, "final_url": url, "body": "", "from_cache": False, "tier": "http",
            "disabled": True,
            "error": f"network disabled; set {ENABLE_FLAG}=1 (or pass --allow-net) to enable",
        }

    result = _http_get(url)
    result.update({"fetched_at": _now_iso(), "from_cache": False, "tier": "http"})
    if result.get("status") == 200:
        _write_cache(root, url, result)
    return result


def get_to_cache(url: str, *, root: Path | None = None, use_cache: bool = True) -> dict[str, Any]:
    """Like ``get`` but writes the body to a cache file and returns its path instead
    of the (potentially huge) body inline — avoids dumping HTML through argv."""
    root = root or _repo_root()
    result = get(url, root=root, use_cache=use_cache)
    body = result.pop("body", "")
    if result.get("status") == 200 and body:
        html_path = _cache_path(root, url).with_suffix(".html")
        html_path.write_text(body, encoding="utf-8")
        result["html_path"] = html_path.as_posix()
        result["body_bytes"] = len(body.encode("utf-8"))
    else:
        result["html_path"] = None
        result["body_bytes"] = 0
    return result


# --- Tier 2: search (DuckDuckGo HTML endpoint) -----------------------------

_RESULT_ANCHOR = re.compile(
    r'<a[^>]*class="[^"]*result__a[^"]*"[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
    re.IGNORECASE | re.DOTALL,
)
_SNIPPET = re.compile(
    r'<a[^>]*class="[^"]*result__snippet[^"]*"[^>]*>(.*?)</a>',
    re.IGNORECASE | re.DOTALL,
)
_TAG = re.compile(r"<[^>]+>")


def _strip(fragment: str) -> str:
    return html.unescape(_TAG.sub("", fragment)).strip()


def _decode_ddg_href(href: str) -> str:
    # DDG HTML wraps targets as /l/?uddg=<urlencoded>
    if "uddg=" in href:
        query = urllib.parse.urlsplit(href).query
        params = urllib.parse.parse_qs(query)
        if params.get("uddg"):
            return params["uddg"][0]
    if href.startswith("//"):
        return "https:" + href
    return href


def search(query: str, *, engine: str = "ddg", max_results: int = 10, root: Path | None = None,
           use_cache: bool = True) -> dict[str, Any]:
    """Run a web search via an allowlisted HTML search endpoint (Tier 2)."""
    root = root or _repo_root()
    if engine not in _SEARCH_ENGINES:
        raise FetchError(f"Unknown search engine: {engine!r}")
    url = _SEARCH_ENGINES[engine].format(q=urllib.parse.quote_plus(query))
    fetched = get(url, root=root, use_cache=use_cache)
    if fetched.get("disabled"):
        return {"query": query, "engine": engine, "results": [], "tier": fetched.get("tier"),
                "disabled": True, "error": fetched.get("error")}
    body = fetched.get("body", "")
    snippets = [_strip(s) for s in _SNIPPET.findall(body)]
    results: list[dict[str, str]] = []
    for index, (href, title) in enumerate(_RESULT_ANCHOR.findall(body)):
        results.append({
            "title": _strip(title),
            "url": _decode_ddg_href(href),
            "snippet": snippets[index] if index < len(snippets) else "",
        })
        if len(results) >= max_results:
            break
    return {
        "query": query, "engine": engine, "status": fetched.get("status"),
        "from_cache": fetched.get("from_cache", False), "tier": fetched.get("tier", "http"),
        "result_count": len(results), "results": results,
    }


# --- Tier 3: headless browser render --------------------------------------


def _browser_helper(root: Path) -> Path:
    return root / ".claude" / "scripts" / "publishing_house" / "net" / "browser_fetch.mjs"


def render(url: str, *, root: Path | None = None, timeout: int = 45) -> dict[str, Any]:
    """Tier 3: render an allowlisted URL in a headless browser via a Node helper.

    Degrades gracefully: if node or the browser is unavailable, returns
    ``{"browser_available": False}`` so the caller can fall back to the manual tier.
    """
    root = root or _repo_root()
    host = _host_of(url)
    if host not in allowed_hosts(root):
        raise FetchError(f"Host not in research-sources allowlist: {host!r}")
    if not _enabled():
        return {"status": 0, "final_url": url, "tier": "browser", "disabled": True,
                "browser_available": "unknown",
                "error": f"network disabled; set {ENABLE_FLAG}=1 to enable"}

    helper = _browser_helper(root)
    if not helper.is_file():
        return {"status": 0, "final_url": url, "tier": "browser", "browser_available": False,
                "error": "browser helper not installed (net/browser_fetch.mjs missing)"}
    import shutil
    node = shutil.which("node")
    if not node:
        return {"status": 0, "final_url": url, "tier": "browser", "browser_available": False,
                "error": "node executable not found"}
    try:
        completed = subprocess.run(  # argument array; never shell=True
            [node, helper.as_posix(), url],
            capture_output=True, text=True, timeout=timeout, check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return {"status": 0, "final_url": url, "tier": "browser", "browser_available": False, "error": str(exc)}
    if completed.returncode != 0:
        stderr = (completed.stderr or "").strip()
        unavailable = "Cannot find" in stderr or "not installed" in stderr or "browserType" in stderr
        return {"status": 0, "final_url": url, "tier": "browser",
                "browser_available": not unavailable, "error": stderr[:500] or "render failed"}
    try:
        payload = json.loads(completed.stdout)
    except ValueError:
        return {"status": 0, "final_url": url, "tier": "browser", "browser_available": True,
                "error": "helper returned non-JSON output"}
    body = payload.get("body", "")
    result = {
        "status": payload.get("status", 200), "final_url": payload.get("final_url", url),
        "tier": "browser", "browser_available": True, "fetched_at": _now_iso(),
    }
    if body:
        html_path = _cache_path(root, url).with_suffix(".browser.html")
        html_path.write_text(body[:MAX_BODY_BYTES], encoding="utf-8")
        result["html_path"] = html_path.as_posix()
        result["body_bytes"] = len(body.encode("utf-8"))
    return result


# --- probe (Tiers 2 -> 3) for one source, used by the doctor ---------------


def probe(source_id: str, *, root: Path | None = None) -> dict[str, Any]:
    """Attempt Tiers 2 then 3 for one configured source; report the best tier."""
    root = root or _repo_root()
    cfg = _sources_config(root)
    source = next((s for s in cfg.get("sources", []) if s.get("id") == source_id), None)
    if source is None:
        raise FetchError(f"Unknown source id: {source_id!r}")
    host = source["host"]
    tiers = source.get("tiers", [])
    checked_at = _now_iso()
    base = {"id": source_id, "host": host, "checked_at": checked_at}

    if not _enabled():
        return {**base, "best_tier": "manual", "status": "unknown",
                "note": f"network disabled ({ENABLE_FLAG}!=1); declared tiers={tiers}"}

    url = f"https://{host}/"
    if "http" in tiers:
        http = get(url, root=root)
        if http.get("status") == 200 and not http.get("disabled"):
            return {**base, "best_tier": "http", "status": "ok"}
    if "browser" in tiers:
        rendered = render(url, root=root)
        if rendered.get("status") == 200 and rendered.get("browser_available") is True:
            return {**base, "best_tier": "browser", "status": "ok"}
        if rendered.get("browser_available") is False:
            base["note"] = "headless browser unavailable"
    # assisted (login) and manual sources cannot be auto-verified
    if "assisted" in tiers:
        return {**base, "best_tier": "assisted", "status": "unknown",
                "note": "data is login-gated; requires interactive human session"}
    return {**base, "best_tier": "manual", "status": "blocked"}
