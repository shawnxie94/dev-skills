"""Unit tests for the no-key web search result hygiene helpers."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "free_web_search", ROOT / "skills" / "free-web-search" / "scripts" / "free_web_search.py"
)
assert SPEC and SPEC.loader
free_web_search = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(free_web_search)


class FreeWebSearchTests(unittest.TestCase):
    def test_domain_values_accept_repeated_and_comma_separated_values(self) -> None:
        self.assertEqual(
            free_web_search._domain_values(["www.tauri.app, docs.rs", "github.com"]),
            ("tauri.app", "docs.rs", "github.com"),
        )

    def test_domain_match_includes_subdomains(self) -> None:
        self.assertTrue(free_web_search._matches_domain("https://v2.tauri.app/docs", "tauri.app"))
        self.assertFalse(free_web_search._matches_domain("https://not-tauri.app/docs", "tauri.app"))

    def test_prepare_results_filters_deduplicates_and_prefers_domains(self) -> None:
        results = [
            {"title": "Other", "href": "https://example.com/a"},
            {"title": "Docs", "href": "https://v2.tauri.app/a#section"},
            {"title": "Duplicate", "href": "https://v2.tauri.app/a/"},
            {"title": "Rust", "href": "https://docs.rs/tauri/latest/"},
        ]

        prepared = free_web_search._prepare_results(
            results,
            domains=(),
            preferred_domains=("docs.rs", "tauri.app"),
        )

        self.assertEqual([result["title"] for result in prepared], ["Rust", "Docs", "Other"])

        filtered = free_web_search._prepare_results(results, domains=("tauri.app",), preferred_domains=())
        self.assertEqual([result["title"] for result in filtered], ["Docs"])


if __name__ == "__main__":
    unittest.main()
