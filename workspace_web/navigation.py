from __future__ import annotations


WORKSPACE_SECTIONS = (
    {
        "id": "dashboard",
        "label": "Dashboard",
        "description": "View local archive stats, coverage gaps, and recent briefings",
        "purpose": "See the health of your local ResearchItem archive at a glance.",
        "reads": "Local ResearchItem sidecars under output/ and recent briefing files under output/briefing/.",
        "produces": "An at-a-glance view of total items, source coverage, missing sources, and recent briefings.",
    },
    {
        "id": "library",
        "label": "Library",
        "description": "Search and browse your local research items",
        "purpose": "Find and inspect items already saved to your local archive.",
        "reads": "Local ResearchItem sidecars under output/ only — never a remote source.",
        "produces": "Filtered lists and per-item detail with a link to the saved Markdown.",
    },
    {
        "id": "briefing",
        "label": "Briefing Workspace",
        "description": "Generate digest or reading list from your archive",
        "purpose": "Turn local items into a digest or reading list you can read or save.",
        "reads": "Local ResearchItem sidecars matching your keyword / sources / date filters.",
        "produces": "A previewable Markdown briefing and, on Save, a file under output/briefing/.",
    },
    {
        "id": "collect",
        "label": "Collect Workspace",
        "description": "Collect research material from GitHub, papers, and WeChat",
        "purpose": "Pull new material from GitHub, arXiv, or WeChat into the local archive.",
        "reads": "Your source-specific inputs (owner/repo, arXiv category, or WeChat URL).",
        "produces": "New ResearchItem sidecars and Markdown files under output/<source>/.",
    },
)


def workspace_sections() -> list[dict[str, str]]:
    return list(WORKSPACE_SECTIONS)


def page_purpose_cards() -> list[dict[str, str]]:
    return [
        {
            "id": section["id"],
            "title": section["label"],
            "purpose": section["purpose"],
            "reads": section["reads"],
            "produces": section["produces"],
        }
        for section in WORKSPACE_SECTIONS
    ]
