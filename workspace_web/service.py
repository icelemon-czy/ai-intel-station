"""Stable public facade for feature-owned Web service modules."""

from .briefing import (
    briefing_action_purposes,
    briefing_flow_notes,
    briefing_mode_purposes,
    preview_briefing,
    save_briefing,
)
from .collect import get_collect_form, list_collect_sources, run_collect
from .dashboard import build_dashboard_overview
from .discovery import (
    discover_status_payload,
    get_job,
    run_discover_from_request,
    start_discover_job,
)
from .library import (
    PreviewError,
    get_library_item_detail,
    library_search_notes,
    list_library_items,
    read_item_markdown,
)
from .navigation import page_purpose_cards, workspace_sections


__all__ = [
    "PreviewError",
    "briefing_action_purposes",
    "briefing_flow_notes",
    "briefing_mode_purposes",
    "build_dashboard_overview",
    "discover_status_payload",
    "get_collect_form",
    "get_job",
    "get_library_item_detail",
    "library_search_notes",
    "list_collect_sources",
    "list_library_items",
    "page_purpose_cards",
    "preview_briefing",
    "read_item_markdown",
    "run_collect",
    "run_discover_from_request",
    "save_briefing",
    "start_discover_job",
    "workspace_sections",
]
