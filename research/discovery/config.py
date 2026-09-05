"""Stable config facade over schema, YAML decoding, validation, and example rendering."""

from __future__ import annotations

from importlib import resources
from pathlib import Path
from typing import Any

import yaml

from .config_schema import (
    DEFAULT_CONFIG_PATH,
    DEFAULT_LOG_DIR,
    DEFAULT_OUTPUT_ROOT,
    EXAMPLE_CONFIG_PATH,
    REPO_ROOT,
    BriefingConfig,
    ConfigError,
    DiscoveryConfig,
    DiscoveryConfigError,
    GitHubSearchQuery,
    GitHubSource,
    HackerNewsSource,
    LimitsConfig,
    PapersSource,
    SourceConfig,
    WeChatAccount,
    WeChatSource,
    XSource,
)
from .config_validation import build_config


class _LocatingLoader(yaml.SafeLoader):
    """Safe YAML loader that records mapping line and column locations."""


def _construct_mapping_with_loc(loader: _LocatingLoader, node: yaml.MappingNode) -> dict:
    loader.flatten_mapping(node)
    mapping = dict(loader.construct_pairs(node, deep=True))
    mapping["__line__"] = node.start_mark.line + 1
    mapping["__col__"] = node.start_mark.column + 1
    return mapping


def _construct_scalar_with_loc(loader: _LocatingLoader, node: yaml.ScalarNode) -> Any:
    value = loader.construct_scalar(node)
    setattr(loader, "_last_scalar", (node.start_mark.line + 1, node.start_mark.column + 1))
    return value


_LocatingLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_mapping_with_loc,
)
_LocatingLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_SCALAR_TAG,
    _construct_scalar_with_loc,
)


def _load_yaml(path: Path | str) -> dict:
    config_path = Path(path)
    if not config_path.is_file():
        raise DiscoveryConfigError(
            f"Config file not found or not a regular file: {config_path}"
        )
    try:
        raw = yaml.load(config_path.read_text(encoding="utf-8"), Loader=_LocatingLoader) or {}
    except yaml.YAMLError as exc:
        raise DiscoveryConfigError(f"Failed to parse YAML at {config_path}: {exc}") from exc
    except OSError as exc:
        raise DiscoveryConfigError(f"Failed to read config at {config_path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise DiscoveryConfigError(
            f"Top-level YAML must be a mapping, got {type(raw).__name__}"
        )
    return raw


def render_example_config() -> str:
    """读取随 package 分发的唯一 Discovery example template。"""

    return resources.files(__package__).joinpath("discovery.yaml.example").read_text(
        encoding="utf-8"
    )


def load_config(path: Path | str) -> DiscoveryConfig:
    """Load YAML and validate it through the single public config surface."""
    return build_config(
        _load_yaml(path),
        repo_root=REPO_ROOT,
        default_output_root=DEFAULT_OUTPUT_ROOT,
        default_log_dir=DEFAULT_LOG_DIR,
    )


__all__ = [
    "BriefingConfig",
    "ConfigError",
    "DEFAULT_CONFIG_PATH",
    "DEFAULT_LOG_DIR",
    "DEFAULT_OUTPUT_ROOT",
    "DiscoveryConfig",
    "DiscoveryConfigError",
    "EXAMPLE_CONFIG_PATH",
    "GitHubSearchQuery",
    "GitHubSource",
    "HackerNewsSource",
    "LimitsConfig",
    "PapersSource",
    "REPO_ROOT",
    "SourceConfig",
    "WeChatAccount",
    "WeChatSource",
    "XSource",
    "load_config",
    "render_example_config",
]
