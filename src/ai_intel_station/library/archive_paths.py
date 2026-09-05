"""Shared source-identity → physical-archive-path rules.

This module is the single owner of the archive organization rule described in
``doc/research_library_design.md``:

- 第一层固定按 source；
- 第二层使用不随分类变化的 stable source identity。

Both the collectors (so a *new* collection writes directly to the target
layout) and the migration planner (so the *existing* archive is reorganized
under the exact same rule) import from here.  There must never be a second
place that computes an ``output/`` archive path.

The functions are pure: they take identity inputs (owner/repo, arxiv id,
canonical URL, title, an explicit timestamp) and return a POSIX path relative
to the output root.  They never touch the network and never read the clock —
callers pass ``collected_at`` in so that planning and tests stay deterministic.
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from pathlib import PurePosixPath

# Sources that own a stable per-item identity live directly under output/<source>/.
SOURCE_DIRS = ("github", "papers", "wechat", "hackernews", "x")

# Reserved sub-namespace that keeps GitHub search snapshots from colliding with
# ``github/<owner>/<repo>`` repository directories at the same level.
GITHUB_SEARCH_NAMESPACE = "_search"
# Reserved sub-namespace for WeChat public-index (watchlist) snapshots so they do
# not mix with per-article ``date-slug-hash`` unit dirs.
WECHAT_INDEX_NAMESPACE = "_index"


def _normalize_timestamp(value: str | None) -> str | None:
    if not value:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def date_component(value: str | None, *, fallback: str = "unknown-date") -> str:
    """Return a stable ``YYYY-MM-DD`` for path display (never ownership)."""
    normalized = _normalize_timestamp(value)
    if not normalized:
        return fallback
    return normalized[:10]


def _timestamp_component(value: str | None) -> str:
    """Return a compact ``YYYYMMDDHHMMSS`` for snapshot identity, or ``manual``."""
    normalized = _normalize_timestamp(value)
    if not normalized:
        return "manual"
    return normalized[:19].replace("-", "").replace(":", "").replace("T", "")


def slugify_title(title: str | None, *, max_length: int = 60) -> str:
    """Build a readable, filesystem-safe slug that keeps CJK and latin words.

    Display only — the stable identity that decides collisions is always a hash
    or a source id, never this slug.
    """
    text = re.sub(r"[/\\?%*:|\"<>\n\r\t]", " ", title or "")
    text = re.sub(r"[^\w一-鿿\- ]", " ", text)
    parts = text.split()
    slug = "-".join(parts)
    slug = re.sub(r"-{2,}", "-", slug).strip("-")
    if not slug:
        return "untitled"
    return slug[:max_length].strip("-") or "untitled"


def short_hash(*parts: str | None) -> str:
    digest = hashlib.sha1("::".join(str(p or "") for p in parts).encode("utf-8")).hexdigest()
    return digest[:8]


def arxiv_identity(canonical_url: str | None, title: str | None = None) -> str:
    """Return the stable ``arxiv-id`` identity for a paper.

    Prefers the id parsed from the canonical ``/abs/<id>`` URL.  Falls back to a
    title-derived slug with a URL/short-hash suffix so a malformed record still
    gets a deterministic, collision-resistant identity (never a bare positional
    index, which is what made the legacy ``NN-Title`` layout unstable).
    """
    url = (canonical_url or "").strip()
    if url:
        tail = url.rstrip("/").rsplit("/", 1)[-1].strip()
        tail = re.sub(r"[?#].*$", "", tail).strip()
        if tail and any(ch.isdigit() for ch in tail):
            # Old-format ids can contain a slash (e.g. ``cs.AI/0101001``); flatten
            # it so the value is usable as a single path component.
            return re.sub(r"[\\/:*?\"<>|]", "-", tail)
    slug = slugify_title(title, max_length=40)
    return f"{slug}-{short_hash(url, title)}"


# --------------------------------------------------------------------------- #
# Leaf identities (relative to a source root, e.g. output/papers)             #
#                                                                             #
# Collectors receive a per-source output dir (``output/<source>``) and compose #
# these leaves onto it. The migration composes the *full* output-root-relative #
# path (``<source>/<leaf>``). Both derive from the same identity primitive so  #
# a freshly collected item and a migrated historical item land in one place.   #
# --------------------------------------------------------------------------- #

def github_repo_leaf(owner: str | None, repo: str | None) -> str:
    return f"{owner or 'unknown-owner'}/{repo or 'unknown-repo'}"


def github_search_leaf(query: str | None, collected_at: str | None = None) -> str:
    normalized = re.sub(r"[^a-z0-9一-鿿]+", "-", (query or "").strip().lower()).strip("-")
    return f"{GITHUB_SEARCH_NAMESPACE}/{normalized or 'query'}-{_timestamp_component(collected_at)}"


def wechat_leaf(title: str | None, canonical_url: str | None, published_at: str | None = None,
                discovered_at: str | None = None) -> str:
    date = date_component(published_at, fallback=date_component(discovered_at, fallback="unknown-date"))
    slug = slugify_title(title, max_length=48)
    return f"{date}-{slug}-{short_hash(canonical_url, title)}"


def wechat_markdown_leaf(title: str | None) -> str:
    return f"{slugify_title(title, max_length=48)}.md"


def wechat_index_leaf(account: str | None, collected_at: str | None = None) -> str:
    """Watchlist public-index snapshots live in a reserved ``_index`` namespace so
    they never collide with per-article ``date-slug-hash`` unit dirs."""
    safe = re.sub(r"[^\w一-鿿\-]+", "-", (account or "account").strip()).strip("-") or "account"
    return f"{WECHAT_INDEX_NAMESPACE}/{safe}-{_timestamp_component(collected_at)}"


def paper_leaf(arxiv_id: str, *, suffix: str = ".md") -> str:
    return f"{arxiv_id}{suffix}"


def hackernews_leaf(item_id: object, *, suffix: str = ".md") -> str:
    return f"{str(item_id or 'unknown').strip() or 'unknown'}{suffix}"


def x_leaf(post_id: object, *, suffix: str = ".md") -> str:
    return f"{str(post_id or 'unknown').strip() or 'unknown'}{suffix}"


# --------------------------------------------------------------------------- #
# Full paths (relative to the output root, e.g. output/)                      #
# --------------------------------------------------------------------------- #

def github_repo_dir(owner: str | None, repo: str | None) -> str:
    return f"github/{github_repo_leaf(owner, repo)}"


def github_search_dir(query: str | None, collected_at: str | None = None) -> str:
    return f"github/{github_search_leaf(query, collected_at)}"


def wechat_unit_dir(title: str | None, canonical_url: str | None, published_at: str | None = None,
                    discovered_at: str | None = None) -> str:
    return f"wechat/{wechat_leaf(title, canonical_url, published_at, discovered_at)}"


def hackernews_item_path(item_id: object, *, suffix: str = ".md") -> str:
    return f"hackernews/{hackernews_leaf(item_id, suffix=suffix)}"


def x_item_path(post_id: object, *, suffix: str = ".md") -> str:
    return f"x/{x_leaf(post_id, suffix=suffix)}"


def paper_item_path(arxiv_id: str, *, suffix: str = ".md") -> str:
    return f"papers/{paper_leaf(arxiv_id, suffix=suffix)}"


def wechat_unit_paths(title: str | None, canonical_url: str | None, published_at: str | None = None,
                      discovered_at: str | None = None) -> dict[str, str]:
    unit = wechat_unit_dir(title, canonical_url, published_at, discovered_at)
    return {
        "dir": unit,
        "markdown": f"{unit}/{wechat_markdown_leaf(title)}",
        "sidecar": f"{unit}/research-item.json",
        "images_dir": f"{unit}/images",
    }


def github_repo_paths(owner: str, repo: str) -> dict[str, str]:
    directory = github_repo_dir(owner, repo)
    return {"dir": directory, "markdown": f"{directory}/README.md", "sidecar": f"{directory}/research-item.json"}


def github_search_paths(query: str, collected_at: str | None) -> dict[str, str]:
    directory = github_search_dir(query, collected_at)
    return {"dir": directory, "markdown": f"{directory}/search.md", "sidecar": f"{directory}/research-items.jsonl"}


def paper_paths(arxiv_id: str) -> dict[str, str]:
    return {"markdown": paper_item_path(arxiv_id), "sidecar": paper_item_path(arxiv_id, suffix=".research-item.json")}


def hackernews_paths(item_id: object) -> dict[str, str]:
    return {"markdown": hackernews_item_path(item_id), "sidecar": hackernews_item_path(item_id, suffix=".research-item.json")}


def x_paths(post_id: object) -> dict[str, str]:
    return {"markdown": x_item_path(post_id), "sidecar": x_item_path(post_id, suffix=".research-item.json")}


def _owner_repo_from_url(url: str | None) -> tuple[str | None, str | None]:
    match = re.match(r"https?://github\.com/([^/]+)/([^/]+?)/?$", (url or "").strip())
    if not match:
        return None, None
    return match.group(1), match.group(2)


def target_markdown_for_item(item) -> str | None:  # item: library.items.ResearchItem
    """Return the target repository-relative markdown path for an existing item.

    This is the migration-facing view of the same organization rule the
    collectors use.  Returns ``None`` when the item has no local primary material
    (e.g. a pure index entry) so the planner can classify it as ``no-op``.
    """
    if not item.output_path:
        return None
    source = item.source
    if source == "github":
        if item.item_type == "search-result":
            # Search results share a snapshot markdown; the snapshot dir is keyed
            # by query + snapshot collection timestamp, which is only knowable at
            # the file level (the migration planner supplies it via
            # ``github_search_dir`` and rewrites the batch's own output_path).
            return None
        owner = item.metadata.get("owner") or _owner_repo_from_url(item.canonical_url)[0]
        repo = item.metadata.get("repo") or _owner_repo_from_url(item.canonical_url)[1]
        if not owner or not repo:
            return None
        return github_repo_paths(owner, repo)["markdown"]
    if source == "papers":
        return paper_paths(arxiv_identity(item.canonical_url, item.title))["markdown"]
    if source == "wechat":
        return wechat_unit_paths(item.title, item.canonical_url, item.published_at, item.discovered_at)["markdown"]
    if source == "hackernews":
        return hackernews_paths(item.metadata.get("item_id"))["markdown"]
    if source == "x":
        return x_paths(item.metadata.get("post_id"))["markdown"]
    return None


def is_target_path(current_output_path: str | None, target: str | None) -> bool:
    if not current_output_path or not target:
        return False
    return PurePosixPath(current_output_path).as_posix() == PurePosixPath(target).as_posix()
