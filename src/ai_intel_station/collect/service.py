from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ai_intel_station.library.service import display_archive_path


GITHUB_SEARCH_FIELDS = (
    "name,owner,description,url,stargazersCount,createdAt,updatedAt"
)


@dataclass(frozen=True)
class CollectionResult:
    """Source-neutral result returned by every standalone collector."""

    source: str
    status: str
    message: str
    summary: str
    next_step: str
    item_count: int = 0
    saved_paths: tuple[str, ...] = ()
    failures: tuple[str, ...] = ()
    details: dict[str, Any] = field(default_factory=dict)

    def to_payload(self) -> dict[str, object]:
        details = {
            "item_count": self.item_count,
            "saved_paths": list(self.saved_paths),
            **self.details,
        }
        if self.failures:
            details["failures"] = list(self.failures)
        return {
            "status": self.status,
            "message": self.message,
            "item_count": self.item_count,
            "saved_paths": list(self.saved_paths),
            "source": self.source,
            "summary": self.summary,
            "next_step": self.next_step,
            "details": details,
        }


def _error(source: str, exc: Exception) -> CollectionResult:
    return CollectionResult(
        source=source,
        status="error",
        message=f"{source} collect failed: {exc}",
        summary=f"{source} collect raised an exception: {type(exc).__name__}: {exc}",
        next_step=(
            "Check your network, the input fields, and any required CLI tools "
            "(gh, camoufox). Then retry."
        ),
        failures=(str(exc),),
        details={"exception": type(exc).__name__, "message": str(exc)},
    )


def collect_github(
    targets: list[str],
    output_root: Path,
    *,
    search: bool = False,
    max_results: int = 10,
) -> CollectionResult:
    import ai_intel_station.collect.github as github

    root = Path(output_root)
    github_root = root / "github"
    try:
        if search:
            query = " ".join(targets).strip()
            if not query:
                return CollectionResult(
                    source="github",
                    status="error",
                    message="GitHub search requires a query",
                    summary="GitHub search was called without a query.",
                    next_step="Enter a search query and retry.",
                )
            raw = github.run_gh(
                [
                    "search",
                    "repos",
                    query,
                    "--sort",
                    "updated",
                    "--limit",
                    str(max_results),
                    "--json",
                    GITHUB_SEARCH_FIELDS,
                ]
            )
            repos = json.loads(raw) if raw.strip() else []
            path = github.save_search_results(query, github_root, repos)
            return CollectionResult(
                source="github",
                status="success",
                message=f"GitHub search for '{query}' completed",
                summary=f"GitHub search for '{query}' returned {len(repos)} repos; saved to output/github/.",
                next_step="Open the Library to browse the new repositories.",
                item_count=len(repos),
                saved_paths=(display_archive_path(path, root),),
                details={"query": query, "max_results": max_results, "search_mode": True},
            )

        saved: list[str] = []
        failures: list[str] = []
        for target in targets:
            if "/" not in target:
                failures.append(f"Skipping '{target}' - expected format: owner/repo")
                continue
            owner, repo = target.split("/", 1)
            if not owner or not repo:
                failures.append(f"Skipping '{target}' - expected format: owner/repo")
                continue
            path = github.save_repo(owner, repo, github_root)
            if path is None:  # test doubles and older adapters may not return the path
                path = github_root / owner / repo / "README.md"
            saved.append(display_archive_path(Path(path), root))

        if not saved:
            message = failures[0] if failures else "GitHub collect requires at least one owner/repo target"
            return CollectionResult(
                source="github",
                status="error",
                message=message,
                summary="No valid GitHub repository target was collected.",
                next_step="Enter one or more targets in owner/repo format, or enable search mode.",
                failures=tuple(failures),
            )
        status = "partial" if failures else "success"
        return CollectionResult(
            source="github",
            status=status,
            message=f"Collected GitHub repo(s): {', '.join(targets)}",
            summary=f"Saved {len(saved)} GitHub repository target(s) to output/github/.",
            next_step="Open the Library to inspect the saved repository Markdown and sidecars.",
            item_count=len(saved),
            saved_paths=tuple(saved),
            failures=tuple(failures),
            details={"targets": list(targets), "search_mode": False},
        )
    except Exception as exc:  # external source boundary
        return _error("github", exc)


def collect_papers(
    categories: list[str],
    output_root: Path,
    *,
    max_results: int = 10,
) -> CollectionResult:
    import ai_intel_station.collect.papers as papers

    if not categories:
        return CollectionResult(
            source="papers",
            status="error",
            message="Please specify at least one category.",
            summary="Paper collection was called without an arXiv category.",
            next_step="Choose a category such as cs.AI and retry.",
        )
    root = Path(output_root)
    saved_paths: list[str] = []
    failures: list[str] = []
    item_count = 0
    completed_categories: list[str] = []

    for category in categories:
        try:
            fetched = papers.fetch_papers_by_category(
                [category],
                max_results=max_results,
                raise_on_error=True,
            )
            completed_categories.append(category)
            if not fetched:
                continue
            papers.save_papers(fetched, category, root / "papers")
            saved_paths.append(f"output/papers/{category}")
            item_count += len(fetched)
        except Exception as exc:  # isolate each external category boundary
            failures.append(f"{category}: {exc}")

    details = {
        "categories": list(categories),
        "completed_categories": completed_categories,
        "max_results": max_results,
    }
    if not completed_categories:
        message = failures[0] if failures else "No arXiv category completed successfully"
        return CollectionResult(
            source="papers",
            status="error",
            message=f"papers collect failed: {message}",
            summary="No requested arXiv category completed successfully.",
            next_step="Check the category names and network, then retry.",
            failures=tuple(failures),
            details=details,
        )

    status = "partial" if failures else "success"
    return CollectionResult(
        source="papers",
        status=status,
        message=f"Collected {item_count} papers from {', '.join(completed_categories)}",
        summary=(
            f"Fetched {item_count} paper(s) from arXiv category "
            f"{', '.join(completed_categories)} and saved them to output/papers/."
        ),
        next_step="Open the Library to read the abstracts and saved Markdown.",
        item_count=item_count,
        saved_paths=tuple(saved_paths),
        failures=tuple(failures),
        details=details,
    )


async def collect_wechat(url: str, output_root: Path) -> CollectionResult:
    import ai_intel_station.collect.wechat as wechat

    if not url:
        return CollectionResult(
            source="wechat",
            status="error",
            message="WeChat collection requires a URL",
            summary="WeChat collect was called without an article URL.",
            next_step="Paste a mp.weixin.qq.com article URL and retry.",
        )
    try:
        normalized = wechat.normalize_wechat_url(url)
        if not normalized.startswith("https://mp.weixin.qq.com/"):
            raise ValueError("Expected an mp.weixin.qq.com article URL")
        path = await wechat.fetch_article(normalized, output_dir=Path(output_root) / "wechat")
        saved_paths = (display_archive_path(Path(path), Path(output_root)),) if isinstance(path, (str, Path)) else ("output/wechat/",)
        return CollectionResult(
            source="wechat",
            status="success",
            message=f"Collected WeChat article: {normalized}",
            summary="Saved the WeChat article to output/wechat/.",
            next_step="Open the Library to read the article Markdown.",
            item_count=1,
            saved_paths=saved_paths,
            details={"url": normalized},
        )
    except Exception as exc:  # optional browser/source boundary
        return _error("wechat", exc)


def run_collection(
    source: str,
    fields: dict[str, object],
    output_root: Path,
) -> CollectionResult:
    """Run one standalone collect operation for CLI or Web adapters."""

    if source == "github":
        query = str(fields.get("query", ""))
        return collect_github(
            [query],
            output_root,
            search=bool(fields.get("search", False)),
            max_results=int(fields.get("max", 10)),
        )
    if source == "papers":
        category = str(fields.get("category", "cs.AI"))
        return collect_papers(
            [category],
            output_root,
            max_results=int(fields.get("max", 10)),
        )
    if source == "wechat":
        return asyncio.run(collect_wechat(str(fields.get("url", "")), output_root))
    return CollectionResult(
        source=source,
        status="error",
        message=f"Unknown source: {source}",
        summary=f"Collect source '{source}' is not supported by this workspace.",
        next_step="Pick one of the supported sources: GitHub, arXiv Papers, or WeChat.",
    )
