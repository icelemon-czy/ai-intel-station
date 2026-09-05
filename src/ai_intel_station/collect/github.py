from __future__ import annotations

import json
import subprocess
from pathlib import Path

from ai_intel_station.library.archive_paths import github_repo_leaf, github_search_leaf
from ai_intel_station.library.items import (
    build_github_repo_item,
    build_github_search_items,
    utc_now_iso,
    write_research_item,
    write_research_items_jsonl,
)


ROOT_DIR = Path(__file__).resolve().parents[3]
OUTPUT_DIR = ROOT_DIR / "output" / "github"


def run_gh(cmd: list[str], *, timeout: float = 30.0) -> str:
    """Run a `gh` CLI subcommand and return its stdout as text.

    Raises ``RuntimeError`` on a non-zero exit, including the captured
    stderr so the CLI can show the underlying message. A hung `gh`
    (for example against a slow network) raises ``subprocess.TimeoutExpired``
    — without the explicit ``timeout`` the workspace would block
    forever on every collect call.
    """
    result = subprocess.run(
        ["gh"] + cmd,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    if result.returncode != 0:
        raise RuntimeError(f"gh failed: {result.stderr.strip()}")
    return result.stdout


def fetch_repo(owner: str, repo: str, *, include_issues: bool = True) -> dict:
    data = json.loads(
        run_gh(
            [
                "repo",
                "view",
                f"{owner}/{repo}",
                "--json",
                "name,description,url,stargazerCount,primaryLanguage,repositoryTopics,createdAt,updatedAt",
            ]
        )
    )
    if include_issues:
        try:
            data["issues"] = json.loads(
                run_gh(
                    [
                        "issue",
                        "list",
                        "-R",
                        f"{owner}/{repo}",
                        "--state",
                        "open",
                        "--limit",
                        "20",
                        "--json",
                        "number,title,state,labels,author,createdAt",
                    ]
                )
            )
        except RuntimeError as exc:
            # Issues fetch failure (auth scope, network, rate limit) is
            # not fatal — the repo meta is still valuable. Surface the
            # issue to operators via the topic-level error reporting
            # without losing the success of the repo save.
            data["issues"] = []
            data.setdefault("_warnings", []).append(
                f"could not list issues: {exc}"
            )
    else:
        data["issues"] = []
    return data


def fetch_readme(owner: str, repo: str) -> str:
    try:
        return run_gh(["repo", "view", f"{owner}/{repo}", "--json", "description"]).strip()
    except Exception:
        return ""


def repo_to_markdown(data: dict, owner: str, repo: str) -> str:
    lines = [
        f"# {data['name']}",
        "",
        f"> {data.get('description', 'No description')}",
        "",
        f"- ⭐ Stars: {data.get('stargazerCount', 'N/A')}",
        f"- 🏷️ Language: {data.get('primaryLanguage', {}).get('name', 'N/A')}",
        f"- 🌐 URL: {data['url']}",
        f"- 📅 Created: {data.get('createdAt', '')[:10]}",
        f"- 🔄 Updated: {data.get('updatedAt', '')[:10]}",
        "",
    ]

    if data.get("repositoryTopics"):
        lines.append("## Topics")
        for topic in data["repositoryTopics"]:
            lines.append(f"- `{topic['topic']['name']}`")
        lines.append("")

    if data.get("issues"):
        lines.append("## Open Issues")
        for issue in data["issues"]:
            labels = [label["name"] for label in issue.get("labels", [])]
            label_str = f" [{', '.join(labels)}]" if labels else ""
            lines.append(f"- [#{issue['number']}]{label_str} {issue['title']} (@{issue['author']['login']})")
        lines.append("")

    return "\n".join(lines)


def save_repo(owner: str, repo: str, output_dir: Path) -> Path:
    """Persist one repository under ``output/github/<owner>/<repo>/``.

    ``output_dir`` is the GitHub source root (``output/github``); the stable
    ``owner/repo`` identity forms the leaf so a repo never moves when its
    topics, stars or collection date change.
    """
    print(f"📦 Fetching {owner}/{repo}...")
    data = fetch_repo(owner, repo)
    repo_dir = Path(output_dir) / github_repo_leaf(owner, repo)
    repo_dir.mkdir(parents=True, exist_ok=True)

    markdown_path = repo_dir / "README.md"
    markdown_path.write_text(repo_to_markdown(data, owner, repo), encoding="utf-8")
    write_research_item(build_github_repo_item(owner, repo, data, markdown_path), repo_dir / "research-item.json")
    print(f"✅ Saved: {markdown_path}")
    return markdown_path

def save_search_results(query: str, output_dir: Path, repos: list[dict], *, collected_at: str | None = None) -> Path:
    """Persist a search snapshot under ``output/github/_search/<query>-<timestamp>/``.

    The snapshot is keyed by normalized query + collection time so repeated
    searches never overwrite an earlier snapshot, while each result keeps its own
    repository identity inside the batch sidecar.
    """
    result_dir = Path(output_dir) / github_search_leaf(query, collected_at or utc_now_iso())
    result_dir.mkdir(parents=True, exist_ok=True)

    lines = [f"# Search: {query}", "", f"Found {len(repos)} repositories", ""]
    for repo in repos:
        lines.append(f"## [{repo['name']}]({repo['url']})")
        lines.append(f"- ⭐ {repo.get('stargazersCount', 0)} stars")
        lines.append(f"- {repo.get('description', 'No description')}")
        lines.append(f"- 📅 Created: {repo.get('createdAt', '')}")
        lines.append(f"- 🔄 Updated: {repo.get('updatedAt', '')}")
        lines.append("")

    markdown_path = result_dir / "search.md"
    markdown_path.write_text("\n".join(lines), encoding="utf-8")
    write_research_items_jsonl(
        build_github_search_items(query, repos, markdown_path),
        result_dir / "research-items.jsonl",
    )
    print(f"✅ Saved search results: {markdown_path}")
    return markdown_path
