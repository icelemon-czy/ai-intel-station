from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class SourceReport:
    name: str
    enabled: bool = False
    skipped: int = 0
    succeeded: int = 0
    failed: int = 0
    output_paths: list[Path] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


@dataclass
class BriefingArtifact:
    path: Path | None
    mode: str
    item_count: int
    status: str


@dataclass
class DiscoveryReport:
    started_at: str
    finished_at: str
    dry_run: bool
    log_path: Path | None
    sources: dict[str, SourceReport] = field(default_factory=dict)
    briefing: BriefingArtifact | None = None

    def to_dict(self) -> dict:
        return {
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "dry_run": self.dry_run,
            "log_path": self.log_path.as_posix() if self.log_path else None,
            "sources": {
                name: {
                    "enabled": report.enabled,
                    "skipped": report.skipped,
                    "succeeded": report.succeeded,
                    "failed": report.failed,
                    "notes": report.notes,
                    "output_paths": [path.as_posix() for path in report.output_paths],
                }
                for name, report in self.sources.items()
            },
            "briefing": (
                {
                    "path": self.briefing.path.as_posix() if self.briefing.path else None,
                    "mode": self.briefing.mode,
                    "item_count": self.briefing.item_count,
                    "status": self.briefing.status,
                }
                if self.briefing
                else None
            ),
        }
