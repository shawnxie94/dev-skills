#!/usr/bin/env python3
"""Small no-key web search and readable-content wrapper for pi skills."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.parse import urlparse
from pathlib import Path


def load_ddgs():
    try:
        from ddgs import DDGS
    except ImportError as exc:
        raise RuntimeError(
            "ddgs is not installed; run: "
            "~/.pi/tools/free-web-search/bin/pip install -U ddgs"
        ) from exc
    return DDGS


def accessed_at() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _domain_values(values: list[str]) -> tuple[str, ...]:
    return tuple(
        value.strip().lower().removeprefix("www.")
        for item in values
        for value in item.split(",")
        if value.strip()
    )


def _host(url: str) -> str:
    return (urlparse(url).hostname or "").lower().removeprefix("www.")


def _matches_domain(url: str, domain: str) -> bool:
    host = _host(url)
    return host == domain or host.endswith(f".{domain}")


def _canonical_url(url: str) -> str:
    parsed = urlparse(url)
    return parsed._replace(fragment="").geturl().rstrip("/").lower()


def _prepare_results(
    results: list[dict[str, object]],
    domains: tuple[str, ...],
    preferred_domains: tuple[str, ...],
) -> list[dict[str, object]]:
    seen: set[str] = set()
    prepared: list[dict[str, object]] = []
    for result in results:
        href = str(result.get("href", ""))
        key = _canonical_url(href)
        if not href or key in seen:
            continue
        if domains and not any(_matches_domain(href, domain) for domain in domains):
            continue
        seen.add(key)
        prepared.append(result)

    if preferred_domains:
        prepared.sort(
            key=lambda result: next(
                (
                    index
                    for index, domain in enumerate(preferred_domains)
                    if _matches_domain(str(result.get("href", "")), domain)
                ),
                len(preferred_domains),
            )
        )
    return prepared


def search(args: argparse.Namespace) -> dict[str, object]:
    DDGS = load_ddgs()
    domains = _domain_values(args.domains)
    preferred_domains = _domain_values(args.prefer_domain)
    backends = (
        [args.backend]
        if args.backend != "auto"
        else ["google", "startpage", "yandex", "bing", "brave", "duckduckgo"]
    )
    errors: list[str] = []
    for backend in backends:
        for attempt in range(args.retries):
            try:
                results = DDGS(timeout=args.timeout).text(
                    args.query,
                    region=args.region,
                    timelimit=args.timelimit,
                    max_results=args.max_results,
                    backend=backend,
                )
                results = _prepare_results(
                    [result for result in results if result.get("href")],
                    domains,
                    preferred_domains,
                )
                if results:
                    return {
                        "query": args.query,
                        "backend": backend,
                        "accessed_at": accessed_at(),
                        "filters": {
                            "domains": list(domains),
                            "prefer_domain": list(preferred_domains),
                        },
                        "results": results,
                    }
                break
            except Exception as exc:
                errors.append(f"{backend}: {exc}")
                if attempt + 1 < args.retries:
                    time.sleep(0.25 * (attempt + 1))
    detail = "; ".join(errors) if errors else "no results"
    raise RuntimeError(f"all search backends failed: {detail}")


def _limit_content(content: str, max_chars: int) -> tuple[str, bool]:
    truncated = len(content) > max_chars
    if truncated:
        content = content[:max_chars].rstrip() + "\n\n[content truncated]"
    return content, truncated


def _defuddle_path() -> str | None:
    configured = os.environ.get("FREE_WEB_SEARCH_DEFUDDLE")
    if configured:
        return configured
    return shutil.which("defuddle") or str(
        Path.home() / ".pi/tools/free-web-search-node/node_modules/.bin/defuddle"
    )


def _fetch_with_defuddle(args: argparse.Namespace) -> dict[str, object]:
    command = _defuddle_path()
    if not command or not Path(command).exists():
        raise FileNotFoundError("defuddle is not installed")

    completed = subprocess.run(
        [command, "parse", args.url, "--markdown", "--json"],
        capture_output=True,
        text=True,
        timeout=args.timeout,
        check=False,
    )
    if completed.returncode != 0:
        detail = completed.stderr.strip()[-1000:] or "unknown error"
        raise RuntimeError(f"defuddle failed: {detail}")
    result = json.loads(completed.stdout)
    content, truncated = _limit_content(str(result.get("content", "")), args.max_chars)
    metadata = {
        key: result.get(key)
        for key in ("author", "description", "domain", "language", "published", "site", "wordCount")
        if result.get(key)
    }
    return {
        "url": args.url,
        "extractor": "defuddle",
        "accessed_at": accessed_at(),
        "title": result.get("title", ""),
        "metadata": metadata,
        "content": content,
        "truncated": truncated,
    }


def _fetch_with_lxml(args: argparse.Namespace) -> dict[str, object]:
    try:
        from lxml import html
    except ImportError as exc:
        raise RuntimeError("neither defuddle nor lxml is available") from exc

    request = Request(
        args.url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; free-web-search/1.0)"},
    )
    with urlopen(request, timeout=args.timeout) as response:
        raw = response.read()

    document = html.fromstring(raw, base_url=args.url)
    for element in document.xpath("//script|//style|//noscript|//svg|//nav|//footer|//aside|//form"):
        element.drop_tree()
    title = " ".join(document.xpath("//title/text()"))
    content, truncated = _limit_content(" ".join(document.text_content().split()), args.max_chars)
    return {
        "url": args.url,
        "extractor": "lxml-fallback",
        "accessed_at": accessed_at(),
        "title": title.strip(),
        "metadata": {},
        "content": content,
        "truncated": truncated,
    }


def fetch(args: argparse.Namespace) -> dict[str, object]:
    parsed = urlparse(args.url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("only http and https URLs are supported")

    try:
        return _fetch_with_defuddle(args)
    except (FileNotFoundError, RuntimeError, json.JSONDecodeError, subprocess.TimeoutExpired):
        # Defuddle is preferred for article extraction; retain a small fallback
        # so the skill remains useful before the optional Node setup is complete.
        return _fetch_with_lxml(args)


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    subparsers = root.add_subparsers(dest="command", required=True)

    search_parser = subparsers.add_parser("search", help="search the public web")
    search_parser.add_argument("query")
    search_parser.add_argument("--max-results", type=int, default=5, choices=range(1, 21))
    search_parser.add_argument("--region", default="us-en")
    search_parser.add_argument("--timelimit", choices=("d", "w", "m", "y"))
    search_parser.add_argument("--backend", default="auto")
    search_parser.add_argument(
        "--domains",
        action="append",
        default=[],
        help="limit results to domains; repeat or use comma-separated values",
    )
    search_parser.add_argument(
        "--prefer-domain",
        action="append",
        default=[],
        help="rank matching domains first; repeat or use comma-separated values",
    )
    search_parser.add_argument("--timeout", type=int, default=15)
    search_parser.add_argument("--retries", type=int, default=2, choices=range(1, 4))
    search_parser.set_defaults(handler=search)

    fetch_parser = subparsers.add_parser("fetch", help="extract readable content from a URL")
    fetch_parser.add_argument("url")
    fetch_parser.add_argument("--max-chars", type=int, default=12000)
    fetch_parser.add_argument("--timeout", type=int, default=15)
    fetch_parser.set_defaults(handler=fetch)
    return root


def main() -> int:
    args = parser().parse_args()
    try:
        payload = args.handler(args)
    except Exception as exc:  # Keep failures visible to the agent and user.
        print(f"free-web-search: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
