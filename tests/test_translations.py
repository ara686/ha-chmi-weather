"""Tests for Home Assistant translation files."""

from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

INTEGRATION_DIR = Path(__file__).parents[1] / "custom_components" / "chmi_weather"
TRANSLATIONS_DIR = INTEGRATION_DIR / "translations"
REQUIRED_LANGUAGES = {"cs", "en", "sk"}


def test_custom_integration_uses_translation_files_only() -> None:
    """Custom integrations should ship per-language translation files."""
    assert not (INTEGRATION_DIR / "strings.json").exists()
    assert REQUIRED_LANGUAGES.issubset(_translation_languages())


def test_translation_files_match_english_keys() -> None:
    """Every shipped language must translate the same keys as English."""
    english_keys = _leaf_key_paths(_load_translation("en"))

    for translation_file in sorted(TRANSLATIONS_DIR.glob("*.json")):
        language = translation_file.stem
        assert _leaf_key_paths(_load_translation(language)) == english_keys


def test_translation_files_do_not_use_build_time_placeholders() -> None:
    """Custom integrations do not run Home Assistant's translation build step."""
    for translation_file in sorted(TRANSLATIONS_DIR.glob("*.json")):
        content = translation_file.read_text(encoding="utf-8")
        assert "[%key:" not in content


def _translation_languages() -> set[str]:
    return {path.stem for path in TRANSLATIONS_DIR.glob("*.json")}


def _load_translation(language: str) -> dict[str, Any]:
    return json.loads((TRANSLATIONS_DIR / f"{language}.json").read_text("utf-8"))


def _leaf_key_paths(data: Mapping[str, Any]) -> set[tuple[str, ...]]:
    return set(_iter_leaf_key_paths(data))


def _iter_leaf_key_paths(
    data: Mapping[str, Any],
    prefix: tuple[str, ...] = (),
) -> Iterable[tuple[str, ...]]:
    for key, value in data.items():
        path = (*prefix, key)
        if isinstance(value, Mapping):
            yield from _iter_leaf_key_paths(value, path)
        else:
            yield path
