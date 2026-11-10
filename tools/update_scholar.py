#!/usr/bin/env python3
"""Fetch citation metrics from the public Google Scholar profile and save them
to scholar.json, which the website reads to show live numbers.

Runs daily from .github/workflows/update-scholar.yml; can also be run by hand:
    python3 tools/update_scholar.py

Google Scholar usually blocks GitHub's servers (HTTP 403). So when the
SERPAPI_KEY environment variable is set (a free key from https://serpapi.com,
stored as a repository secret), the script falls back to SerpApi's Google
Scholar Author API, which returns the same numbers.

Standard library only. If every source fails, scholar.json is left untouched
so the site keeps the last good numbers.
"""
import html
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

SCHOLAR_ID = "hZgi4BgAAAAJ"
OUT = Path(__file__).resolve().parent.parent / "scholar.json"
URL = "https://scholar.google.com/citations?user={id}&hl=en&cstart={start}&pagesize=100"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}


def warn(msg):
    # Shows as a yellow annotation in GitHub Actions without failing the run
    print(f"::warning::{msg}")


def fetch(start):
    req = urllib.request.Request(URL.format(id=SCHOLAR_ID, start=start), headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def text(s):
    return html.unescape(re.sub(r"<[^>]+>", "", s)).strip()


def num(s):
    s = text(s)
    return int(s) if s.isdigit() else 0


def parse_stats(page):
    table = re.search(r'<table id="gsc_rsb_st">(.*?)</table>', page, re.S)
    if not table:
        return None
    since = re.findall(r'<th class="gsc_rsb_sth">(.*?)</th>', table.group(1))
    rows = re.findall(r'<td class="gsc_rsb_sc1">(.*?)</td>\s*<td class="gsc_rsb_std">(\d*)</td>\s*<td class="gsc_rsb_std">(\d*)</td>',
                      table.group(1), re.S)
    stats = {}
    for label, all_, recent in rows:
        name = text(label).lower().replace("-", "_")
        stats[name] = {"all": int(all_ or 0), "recent": int(recent or 0)}
    if not {"citations", "h_index", "i10_index"} <= stats.keys():
        return None
    stats["recent_label"] = text(since[-1]) if since else "Recent"
    return stats


def parse_history(page):
    years = [int(y) for y in re.findall(r'<span class="gsc_g_t"[^>]*>(\d{4})</span>', page)]
    counts = [int(c) for c in re.findall(r'<span class="gsc_g_al">(\d+)</span>', page)]
    # Scholar omits bars for years with zero citations; only trust a clean match
    return [{"year": y, "citations": c} for y, c in zip(years, counts)] if len(years) == len(counts) else []


def parse_papers(page):
    papers = []
    for row in re.findall(r'<tr class="gsc_a_tr">(.*?)</tr>', page, re.S):
        title = re.search(r'class="gsc_a_at">(.*?)</a>', row, re.S)
        cites = re.search(r'class="gsc_a_ac gs_ibl">(.*?)</a>', row, re.S)
        year = re.search(r'class="gsc_a_h[^"]*">(\d{4})?</span>', row)
        if title:
            papers.append({
                "title": text(title.group(1)),
                "citations": num(cites.group(1)) if cites else 0,
                "year": int(year.group(1)) if year and year.group(1) else None,
            })
    return papers


def from_scholar():
    """Scrape the public profile page directly. Returns (stats, history, papers)."""
    first = fetch(0)
    stats = parse_stats(first)
    if not stats:
        raise RuntimeError("page did not contain the metrics table (blocked or layout changed)")
    papers = parse_papers(first)
    start = 100
    while len(papers) == start:  # profile has more than one page of papers
        time.sleep(3)
        try:
            more = parse_papers(fetch(start))
        except Exception:
            break
        if not more:
            break
        papers.extend(more)
        start += 100
    return stats, parse_history(first), papers


def from_serpapi(key):
    """Same data via SerpApi's Google Scholar Author API (works from GitHub Actions)."""
    def get(start):
        q = urllib.parse.urlencode({"engine": "google_scholar_author", "author_id": SCHOLAR_ID,
                                    "hl": "en", "num": 100, "start": start, "api_key": key})
        with urllib.request.urlopen("https://serpapi.com/search.json?" + q, timeout=60) as r:
            return json.load(r)

    first = get(0)
    if first.get("error"):
        raise RuntimeError(first["error"])
    stats, recent_label = {}, "Recent"
    for row in first.get("cited_by", {}).get("table", []):
        for name, vals in row.items():
            since = next((k for k in vals if k.startswith("since_")), None)
            if since:
                recent_label = "Since " + since.split("_", 1)[1]
            stats[name] = {"all": int(vals.get("all", 0)), "recent": int(vals.get(since, 0)) if since else 0}
    if not {"citations", "h_index", "i10_index"} <= stats.keys():
        raise RuntimeError("response did not contain the metrics table")
    stats["recent_label"] = recent_label
    history = [{"year": int(g["year"]), "citations": int(g.get("citations", 0))}
               for g in first.get("cited_by", {}).get("graph", [])]

    def articles(page):
        return [{
            "title": a.get("title", "").strip(),
            "citations": int((a.get("cited_by") or {}).get("value") or 0),
            "year": int(a["year"]) if str(a.get("year", "")).isdigit() else None,
        } for a in page.get("articles", [])]

    papers, page, start = articles(first), first, 100
    while page.get("serpapi_pagination", {}).get("next") and start < 1000:
        page = get(start)
        if not page.get("articles"):
            break
        papers.extend(articles(page))
        start += 100
    return stats, history, papers


def main():
    try:
        stats, history, papers = from_scholar()
    except Exception as e:  # HTTP 403/429, captcha page, network error, ...
        key = os.environ.get("SERPAPI_KEY", "").strip()
        if not key:
            warn(f"Could not read Google Scholar ({e}) and no SERPAPI_KEY secret is set; keeping previous scholar.json")
            return 0
        print(f"Google Scholar refused the request ({e}); using SerpApi instead.")
        try:
            stats, history, papers = from_serpapi(key)
        except Exception as e2:
            warn(f"SerpApi also failed ({e2}); keeping previous scholar.json")
            return 0

    data = {
        "source": f"https://scholar.google.com/citations?user={SCHOLAR_ID}",
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "citations": stats["citations"]["all"],
        "h_index": stats["h_index"]["all"],
        "i10_index": stats["i10_index"]["all"],
        "recent": {
            "label": stats["recent_label"],
            "citations": stats["citations"]["recent"],
            "h_index": stats["h_index"]["recent"],
            "i10_index": stats["i10_index"]["recent"],
        },
        "history": history,
        "papers": sorted(papers, key=lambda p: -p["citations"]),
    }

    # Avoid daily commits when only the timestamp would change
    if OUT.exists():
        old = json.loads(OUT.read_text(encoding="utf-8"))
        if {k: v for k, v in old.items() if k != "updated"} == {k: v for k, v in data.items() if k != "updated"}:
            print("No change in Scholar metrics.")
            return 0

    OUT.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Updated: {data['citations']} citations, h-index {data['h_index']}, "
          f"i10-index {data['i10_index']}, {len(papers)} papers")
    return 0


if __name__ == "__main__":
    sys.exit(main())
