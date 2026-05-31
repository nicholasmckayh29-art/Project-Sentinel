"""Ingest AI market news and events from open sources into normalized event dicts."""

from __future__ import annotations

import json
import logging
import os
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any
from urllib.parse import quote
from urllib.request import Request, urlopen

log = logging.getLogger(__name__)

HN_ALGOLIA = "https://hn.algolia.com/api/v1/search"
ARXIV_API = "http://export.arxiv.org/api/query"
OPENALEX = "https://api.openalex.org/works"
GITHUB_API = "https://api.github.com/repos/{repo}/releases"
BSKY_SEARCH = "https://public.api.bsky.app/xrpc/app.bsky.feed.searchPosts"
DEVTO_API = "https://dev.to/api/articles"
MARKETAUX = "https://api.marketaux.com/v1/news/all"
SEC_SUBMISSIONS = "https://data.sec.gov/submissions/CIK{cik}.json"

RSS_FEEDS = [
    ("MIT Technology Review", "https://www.technologyreview.com/feed/"),
    ("Ars Technica", "https://feeds.arstechnica.com/arstechnica/technology-lab"),
    ("Google News AI", "https://news.google.com/rss/search?q=artificial+intelligence&hl=en-US&gl=US&ceid=US:en"),
]

GITHUB_REPOS = [
    "openai/openai-python",
    "anthropics/anthropic-sdk-python",
    "meta-llama/llama-models",
    "vllm-project/vllm",
    "langchain-ai/langchain",
    "ollama/ollama",
]

HN_QUERIES = ["AI", "LLM", "OpenAI", "Anthropic"]
ARXIV_KEYWORDS = re.compile(
    r"\b(llm|large language|transformer|gpt|claude|inference|benchmark)\b", re.I
)
SENTIMENT_BULLISH = re.compile(r"\b(benchmark|sota|breakthrough|launch|funding)\b", re.I)
SENTIMENT_BEARISH = re.compile(r"\b(price cut|layoff|regulation|ban|safety concern)\b", re.I)

SEC_CIKS = {
    "NVDA": "0001045810",
    "MSFT": "0000789019",
    "GOOGL": "0001652044",
    "META": "0001326801",
    "AMZN": "0001018724",
    "AMD": "0000002488",
}


def _fetch_json(url: str, headers: dict[str, str] | None = None, timeout: int = 25) -> Any:
    req_headers = {"User-Agent": "pricing-sentinel/1.0", **(headers or {})}
    request = Request(url, headers=req_headers)
    with urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _fetch_text(url: str, headers: dict[str, str] | None = None, timeout: int = 25) -> str:
    req_headers = {"User-Agent": "pricing-sentinel/1.0", **(headers or {})}
    request = Request(url, headers=req_headers)
    with urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def _sentiment_hint(text: str) -> str:
    if SENTIMENT_BEARISH.search(text):
        return "bearish"
    if SENTIMENT_BULLISH.search(text):
        return "bullish"
    return "neutral"


def _keywords_matched(text: str) -> list[str]:
    found = []
    for pattern in (SENTIMENT_BULLISH, SENTIMENT_BEARISH, ARXIV_KEYWORDS):
        for match in pattern.finditer(text):
            word = match.group(0).lower()
            if word not in found:
                found.append(word)
    return found[:5]


def fetch_hn_algolia() -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    seen: set[str] = set()
    for query in HN_QUERIES:
        try:
            url = f"{HN_ALGOLIA}?query={quote(query)}&tags=story&hitsPerPage=15"
            payload = _fetch_json(url)
            for hit in payload.get("hits", []):
                story_url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}"
                if story_url in seen:
                    continue
                seen.add(story_url)
                title = hit.get("title") or "Untitled"
                points = hit.get("points") or 0
                events.append(
                    {
                        "title": title,
                        "summary": f"HN · {points} points",
                        "event_type": "news",
                        "source": "Hacker News",
                        "url": story_url,
                        "published_at": datetime.fromtimestamp(
                            hit.get("created_at_i", 0), tz=timezone.utc
                        ).isoformat(),
                        "metadata": {
                            "source_api": "hn_algolia",
                            "hn_points": points,
                            "sentiment_hint": _sentiment_hint(title),
                            "keywords_matched": _keywords_matched(title),
                        },
                    }
                )
        except Exception as exc:
            log.warning("HN Algolia fetch failed for %s: %s", query, exc)
    return events


def fetch_rss_feeds() -> list[dict[str, Any]]:
    try:
        import feedparser
    except ImportError:
        log.warning("feedparser not installed — skipping RSS")
        return []

    events: list[dict[str, Any]] = []
    seen: set[str] = set()
    for source_name, feed_url in RSS_FEEDS:
        try:
            parsed = feedparser.parse(feed_url)
            for entry in parsed.entries[:12]:
                link = entry.get("link")
                if not link or link in seen:
                    continue
                title = entry.get("title", "")
                if not re.search(r"\b(ai|artificial intelligence|llm|machine learning|openai|anthropic)\b", title, re.I):
                    if source_name != "Google News AI":
                        continue
                seen.add(link)
                published = entry.get("published_parsed") or entry.get("updated_parsed")
                if published:
                    published_at = datetime(*published[:6], tzinfo=timezone.utc).isoformat()
                else:
                    published_at = datetime.now(timezone.utc).isoformat()
                events.append(
                    {
                        "title": title,
                        "summary": entry.get("summary", "")[:280] or None,
                        "event_type": "news",
                        "source": source_name,
                        "url": link,
                        "published_at": published_at,
                        "metadata": {
                            "source_api": "rss",
                            "sentiment_hint": _sentiment_hint(title),
                            "keywords_matched": _keywords_matched(title),
                        },
                    }
                )
        except Exception as exc:
            log.warning("RSS fetch failed for %s: %s", source_name, exc)
    return events


def fetch_release_feed() -> list[dict[str, Any]]:
    from backend.engine.check_releases import RELEASE_FEED_URL, fetch_release_feed as _fetch

    events: list[dict[str, Any]] = []
    for item in _fetch()[:20]:
        title = item.get("title") or item.get("name", "Unknown release")
        events.append(
            {
                "title": title,
                "summary": item.get("summary") or "New model release",
                "event_type": "release",
                "source": "pricetoken",
                "url": item.get("url") or RELEASE_FEED_URL,
                "published_at": item.get("published_at")
                or item.get("date")
                or datetime.now(timezone.utc).isoformat(),
                "metadata": {
                    "source_api": "pricetoken_feed",
                    "models_affected": item.get("models", []),
                    "sentiment_hint": "bullish",
                },
            }
        )
    return events


def fetch_arxiv() -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    try:
        query = "cat:cs.CL OR cat:cs.LG"
        url = f"{ARXIV_API}?search_query={quote(query)}&sortBy=submittedDate&sortOrder=descending&max_results=25"
        text = _fetch_text(url)
        root = ET.fromstring(text)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        for entry in root.findall("atom:entry", ns):
            title = (entry.find("atom:title", ns).text or "").strip().replace("\n", " ")
            if not ARXIV_KEYWORDS.search(title):
                continue
            arxiv_id = entry.find("atom:id", ns).text.split("/abs/")[-1]
            summary_el = entry.find("atom:summary", ns)
            summary = (summary_el.text or "").strip()[:280] if summary_el is not None else None
            published_el = entry.find("atom:published", ns)
            published_at = published_el.text if published_el is not None else datetime.now(timezone.utc).isoformat()
            events.append(
                {
                    "title": title,
                    "summary": summary,
                    "event_type": "research",
                    "source": "arXiv",
                    "url": f"https://arxiv.org/abs/{arxiv_id}",
                    "published_at": published_at,
                    "metadata": {
                        "source_api": "arxiv",
                        "arxiv_id": arxiv_id,
                        "sentiment_hint": _sentiment_hint(title),
                        "keywords_matched": _keywords_matched(title),
                    },
                }
            )
    except Exception as exc:
        log.warning("arXiv fetch failed: %s", exc)
    return events


def fetch_openalex() -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    try:
        url = f"{OPENALEX}?search={quote('large language model')}&sort=publication_date:desc&per_page=15"
        payload = _fetch_json(url)
        for work in payload.get("results", []):
            title = work.get("title") or "Untitled"
            if not ARXIV_KEYWORDS.search(title):
                continue
            landing = work.get("doi") or work.get("id")
            events.append(
                {
                    "title": title,
                    "summary": (work.get("abstract_inverted_index") and "Research paper") or None,
                    "event_type": "research",
                    "source": "OpenAlex",
                    "url": landing if landing.startswith("http") else f"https://openalex.org/{work.get('id', '')}",
                    "published_at": work.get("publication_date") or datetime.now(timezone.utc).isoformat(),
                    "metadata": {
                        "source_api": "openalex",
                        "openalex_id": work.get("id"),
                        "sentiment_hint": _sentiment_hint(title),
                    },
                }
            )
    except Exception as exc:
        log.warning("OpenAlex fetch failed: %s", exc)
    return events


def fetch_github_releases() -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    token = os.environ.get("GITHUB_TOKEN")
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    for repo in GITHUB_REPOS:
        try:
            url = GITHUB_API.format(repo=repo)
            releases = _fetch_json(url, headers=headers)
            if not isinstance(releases, list):
                continue
            for release in releases[:2]:
                events.append(
                    {
                        "title": f"{repo} {release.get('tag_name', '')}",
                        "summary": (release.get("body") or "")[:280] or None,
                        "event_type": "release",
                        "source": "GitHub",
                        "url": release.get("html_url") or f"https://github.com/{repo}/releases",
                        "published_at": release.get("published_at") or datetime.now(timezone.utc).isoformat(),
                        "metadata": {
                            "source_api": "github",
                            "repo": repo,
                            "tag": release.get("tag_name"),
                            "sentiment_hint": "bullish",
                        },
                    }
                )
        except Exception as exc:
            log.warning("GitHub releases failed for %s: %s", repo, exc)
    return events


def fetch_devto() -> list[dict[str, Any]]:
    api_key = os.environ.get("DEVTO_API_KEY")
    if not api_key:
        return []
    events: list[dict[str, Any]] = []
    try:
        for tag in ("ai", "machinelearning"):
            url = f"{DEVTO_API}?tag={tag}&per_page=10"
            articles = _fetch_json(url, headers={"api-key": api_key})
            for article in articles:
                events.append(
                    {
                        "title": article.get("title", ""),
                        "summary": article.get("description"),
                        "event_type": "dev_article",
                        "source": "Dev.to",
                        "url": article.get("url"),
                        "published_at": article.get("published_at") or datetime.now(timezone.utc).isoformat(),
                        "metadata": {
                            "source_api": "devto",
                            "tag": tag,
                            "sentiment_hint": _sentiment_hint(article.get("title", "")),
                        },
                    }
                )
    except Exception as exc:
        log.warning("Dev.to fetch failed: %s", exc)
    return events


def fetch_bluesky() -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for term in ("LLM", "GPT-4", "Claude"):
        try:
            url = f"{BSKY_SEARCH}?q={quote(term)}&limit=10"
            payload = _fetch_json(url)
            for post in payload.get("posts", []):
                record = post.get("record", {})
                text = record.get("text", "")
                uri = post.get("uri", "")
                handle = post.get("author", {}).get("handle", "unknown")
                events.append(
                    {
                        "title": text[:120] + ("…" if len(text) > 120 else ""),
                        "summary": f"@{handle}",
                        "event_type": "social",
                        "source": "Bluesky",
                        "url": f"https://bsky.app/profile/{handle}/post/{uri.split('/')[-1]}" if uri else None,
                        "published_at": record.get("createdAt") or datetime.now(timezone.utc).isoformat(),
                        "metadata": {
                            "source_api": "bluesky",
                            "search_term": term,
                            "sentiment_hint": _sentiment_hint(text),
                        },
                    }
                )
        except Exception as exc:
            log.warning("Bluesky fetch failed for %s: %s", term, exc)
    return events


def fetch_marketaux() -> list[dict[str, Any]]:
    api_key = os.environ.get("MARKETAUX_API_KEY")
    if not api_key:
        return []
    events: list[dict[str, Any]] = []
    try:
        symbols = "NVDA,MSFT,GOOGL,META,AMZN,AMD"
        url = f"{MARKETAUX}?symbols={symbols}&filter_entities=true&language=en&api_token={api_key}"
        payload = _fetch_json(url)
        for item in payload.get("data", [])[:20]:
            entities = item.get("entities") or []
            tickers = [e.get("symbol") for e in entities if e.get("symbol")]
            sentiment = (item.get("sentiment") or "neutral").lower()
            events.append(
                {
                    "title": item.get("title", ""),
                    "summary": item.get("description", "")[:280] or None,
                    "event_type": "news",
                    "source": item.get("source") or "MarketAux",
                    "url": item.get("url"),
                    "published_at": item.get("published_at") or datetime.now(timezone.utc).isoformat(),
                    "metadata": {
                        "source_api": "marketaux",
                        "tickers": tickers,
                        "sentiment_hint": sentiment,
                    },
                }
            )
    except Exception as exc:
        log.warning("MarketAux fetch failed: %s", exc)
    return events


def fetch_sec_filings() -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    headers = {"User-Agent": "PricingSentinel contact@example.com"}
    for symbol, cik in SEC_CIKS.items():
        try:
            url = SEC_SUBMISSIONS.format(cik=cik)
            payload = _fetch_json(url, headers=headers)
            recent = payload.get("filings", {}).get("recent", {})
            forms = recent.get("form", [])
            dates = recent.get("filingDate", [])
            accessions = recent.get("accessionNumber", [])
            for i, form in enumerate(forms[:5]):
                if form not in ("8-K", "10-K", "10-Q"):
                    continue
                accession = accessions[i].replace("-", "")
                events.append(
                    {
                        "title": f"{symbol} filed {form}",
                        "summary": payload.get("name"),
                        "event_type": "filing",
                        "source": "SEC EDGAR",
                        "url": f"https://www.sec.gov/Archives/edgar/data/{cik.lstrip('0')}/{accession}",
                        "published_at": datetime.strptime(dates[i], "%Y-%m-%d").replace(tzinfo=timezone.utc).isoformat(),
                        "metadata": {
                            "source_api": "sec_edgar",
                            "tickers": [symbol],
                            "form": form,
                            "sentiment_hint": "neutral",
                        },
                    }
                )
                break
        except Exception as exc:
            log.warning("SEC EDGAR fetch failed for %s: %s", symbol, exc)
    return events


def enrich_og_previews(events: list[dict[str, Any]], limit: int = 15) -> None:
    """Fetch Microlink OG metadata for recent events missing og cache."""
    enriched = 0
    for event in events:
        if enriched >= limit:
            break
        url = event.get("url")
        if not url or event.get("metadata", {}).get("og"):
            continue
        try:
            api_url = f"https://api.microlink.io?url={quote(url)}"
            payload = _fetch_json(api_url)
            data = payload.get("data", {})
            event.setdefault("metadata", {})["og"] = {
                "title": data.get("title"),
                "description": data.get("description"),
                "image": data.get("image", {}).get("url") if isinstance(data.get("image"), dict) else data.get("image"),
            }
            enriched += 1
        except Exception:
            continue


def ingest_all(*, enrich_og: bool = True) -> list[dict[str, Any]]:
    """Collect events from all configured sources."""
    collectors = [
        fetch_hn_algolia,
        fetch_rss_feeds,
        fetch_release_feed,
        fetch_arxiv,
        fetch_openalex,
        fetch_github_releases,
        fetch_devto,
        fetch_bluesky,
        fetch_marketaux,
        fetch_sec_filings,
    ]
    all_events: list[dict[str, Any]] = []
    seen_urls: set[str] = set()
    for collector in collectors:
        for event in collector():
            url = event.get("url")
            if url and url in seen_urls:
                continue
            if url:
                seen_urls.add(url)
            all_events.append(event)

    if enrich_og:
        enrich_og_previews(all_events)

    log.info("Ingested %d market events from %d sources", len(all_events), len(collectors))
    return all_events
