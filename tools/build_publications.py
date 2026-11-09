#!/usr/bin/env python3
"""Regenerate the publication list from publications.bib.

Usage (from the repository root):
    python3 tools/build_publications.py

It rewrites:
  * the list between the PUBLICATIONS markers in publications.html
  * the window.publications array between the markers in script.js

To add a paper: add its BibTeX entry to publications.bib, add a line for its
key in META below (type, link), then run the script. No dependencies needed.
"""
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SELF_NAMES = {"Kushagra Agrawal", "K. Agrawal"}

# type: journal | conference | workshop | book | preprint | patent
# url: paper link (leave None to show a Google Scholar search link instead)
META = {
    "agrawal2026multiomics": ("journal", None),
    "agrawal2026artificial": ("journal", "https://doi.org/10.1039/d6fo02990f"),
    "chakraborty2026indisegnet": ("journal", "https://www.sciencedirect.com/science/article/pii/S2667305326000049"),
    "agrawal2026translating": ("workshop", None),
    "agrawal2026token": ("workshop", "https://lnkd.in/dCUdAAbi"),
    "agrawal2026structured": ("conference", None),
    "agrawal2026awraf": ("conference", None),
    "agrawal2026optimization": ("conference", "https://doi.org/10.1007/978-3-032-16632-6_24"),
    "agrawal2026quantitative": ("conference", "https://doi.org/10.1109/HiPCW66559.2025.00023"),
    "agrawal2026behavioural": ("book", "https://doi.org/10.2174/9798898813932126030011"),
    "agrawal2026ai": ("book", "https://www.taylorfrancis.com/chapters/edit/10.1201/9781003541875-1/ai-driven-demand-forecasting-industry-4-0-techniques-applications-future-trends-kushagra-agrawal-polat-goktas"),
    "agrawal2026detection": ("book", "https://www.sciencedirect.com/science/chapter/edited-volume/abs/pii/B978044326468900045X"),
    "agrawal2026novel": ("book", "https://www.sciencedirect.com/science/chapter/edited-volume/abs/pii/B9780443333453000067"),
    "agrawal2025ai": ("journal", "https://www.frontiersin.org/journals/nutrition/articles/10.3389/fnut.2025.1553942/full"),
    "agrawal2025artificial": ("journal", "https://www.frontiersin.org/articles/10.3389/fnut.2025.1636980/full"),
    "agrawal2025neural": ("conference", "https://link.springer.com/chapter/10.1007/978-3-032-18477-1_55"),
    "agrawal2025trust": ("conference", "https://doi.org/10.1109/ICEdge67252.2025.11412888"),
    "k2025enhancing": ("conference", "https://arxiv.org/abs/2505.02861"),
    "agrawal2025machine": ("book", "https://www.taylorfrancis.com/chapters/edit/10.1201/9781003531791-8/machine-vision-deep-learning-meat-processing-kushagra-agrawal-cyrine-abid-navneet-kumar-polat-goktas"),
    "agrawal2025large": ("book", "https://link.springer.com/chapter/10.1007/978-3-031-86039-3_8"),
    "agrawal2025aiml": ("book", "https://link.springer.com/chapter/10.1007/978-3-031-76758-6_2"),
    "agrawal2025aiiot": ("book", "https://onlinelibrary.wiley.com/doi/abs/10.1002/9781394337262.ch02"),
    "agrawal2025artificialagri": ("book", "https://onlinelibrary.wiley.com/doi/abs/10.1002/9781394320905.ch04"),
    "agrawal2025computer": ("book", "https://onlinelibrary.wiley.com/doi/abs/10.1002/9781394320905.ch03"),
    "agrawal2025mohaf": ("preprint", "https://arxiv.org/abs/2508.14830"),
    "mohantydynamic": ("preprint", None),
    "agrawal2025methodological": ("patent", "https://iprsearch.ipindia.gov.in/publicsearch"),
    "agrawal2024deep": ("conference", "https://link.springer.com/chapter/10.1007/978-3-031-50583-6_15"),
    "agrawal2024advancements": ("conference", "https://iopscience.iop.org/article/10.1088/1742-6596/2818/1/012040"),
    "agrawal2024iot": ("conference", "https://link.springer.com/chapter/10.1007/978-3-031-81404-4_4"),
    "agrawal2024optimizing": ("conference", "https://link.springer.com/chapter/10.1007/978-981-95-1069-6_16"),
    "agrawal2023artificial": ("conference", "https://ieeexplore.ieee.org/document/10404183"),
    "agrawal2023advancements": ("conference", None),
}

# Optional display tweaks (venue text shown on the site; BibTeX is untouched)
VENUE_OVERRIDE = {
    "agrawal2026token": "Second Workshop on Agents in the Wild: Safety, Security, and Beyond (AI-Wild @ ICML 2026)",
    "agrawal2026translating": "Proceedings of the Second Workshop for REsearch on Agent Language Models (REALM @ EMNLP 2026)",
    "mohantydynamic": "Preprint",
    "agrawal2025mohaf": "arXiv preprint arXiv:2508.14830",
    "k2025enhancing": "International Conference on Innovative Computing & Communication in Life Sciences, Agriculture and Technology (CCS University, Meerut)",
}
YEAR_OVERRIDE = {"mohantydynamic": "2025"}

TYPE_INFO = {
    "journal": ("type-journal", "tag-journal", "fa-newspaper", "Journal Paper"),
    "conference": ("type-conference", "tag-conference", "fa-users", "Conference"),
    "workshop": ("type-conference", "tag-conference", "fa-users", "Workshop"),
    "book": ("type-book", "tag-book-chapter", "fa-book", "Book Chapter"),
    "preprint": ("type-preprint", "tag-preprint", "fa-file-lines", "Preprint"),
    "patent": ("type-patent", "tag-patent", "fa-lightbulb", "Patent"),
}
TYPE_ORDER = ["journal", "conference", "workshop", "book", "patent", "preprint"]


def parse_bib(text):
    entries = []
    for m in re.finditer(r"@(\w+)\s*\{\s*([^,\s]+)\s*,", text):
        start = m.start()
        depth, i = 0, text.index("{", m.start())
        while i < len(text):
            if text[i] == "{":
                depth += 1
            elif text[i] == "}":
                depth -= 1
                if depth == 0:
                    break
            i += 1
        raw = text[start:i + 1]
        body = text[m.end():i]
        fields = {}
        for fm in re.finditer(r"(\w+)\s*=\s*", body):
            j = fm.end()
            if j < len(body) and body[j] == "{":
                d, k = 0, j
                while k < len(body):
                    if body[k] == "{":
                        d += 1
                    elif body[k] == "}":
                        d -= 1
                        if d == 0:
                            break
                    k += 1
                fields[fm.group(1).lower()] = body[j + 1:k]
        entries.append({"kind": m.group(1).lower(), "key": m.group(2), "fields": fields, "raw": raw})
    return entries


def clean(s):
    s = s.replace("\\&", "&").replace("``", "“").replace("''", "”").replace("--", "–")
    s = re.sub(r"[{}]", "", s)
    return " ".join(s.split())


def authors(s):
    out = []
    for a in s.split(" and "):
        a = clean(a)
        if "," in a:
            last, first = [p.strip() for p in a.split(",", 1)]
            a = f"{first} {last}"
        out.append(a)
    return out


def build():
    bib = (ROOT / "publications.bib").read_text(encoding="utf-8")
    pubs = []
    for e in parse_bib(bib):
        f, key = e["fields"], e["key"]
        if key not in META:
            raise SystemExit(f"Add '{key}' to META in tools/build_publications.py")
        ptype, url = META[key]
        venue = VENUE_OVERRIDE.get(key) or clean(f.get("journal") or f.get("booktitle") or f.get("note") or "")
        details = []
        if f.get("volume") and ptype != "conference":
            details.append(f"Vol. {clean(f['volume'])}")
        if f.get("pages"):
            pages = clean(f["pages"])
            details.append(("pp. " if "–" in pages else "Art. " if len(pages) > 4 else "p. ") + pages)
        publisher = clean(f.get("publisher") or f.get("organization") or "")
        if publisher and not publisher.startswith("http"):
            details.append(publisher)
        year = YEAR_OVERRIDE.get(key) or clean(f.get("year", ""))
        pubs.append({
            "key": key, "type": ptype, "title": clean(f.get("title", "")),
            "authors": authors(f.get("author", "")), "venue": venue,
            "details": details, "year": year, "url": url, "raw": e["raw"].strip(),
        })

    pubs.sort(key=lambda p: (-int(p["year"] or 0), TYPE_ORDER.index(p["type"])))
    return pubs


def render_html(pubs):
    out, current = [], None
    for p in pubs:
        if p["year"] != current:
            current = p["year"]
            out.append(f'\n                <h2 class="year-heading">{current}</h2>\n')
        cls, tag, icon, label = TYPE_INFO[p["type"]]
        title = html.escape(p["title"])
        if p["url"]:
            title_html = f'<a href="{html.escape(p["url"])}" target="_blank" rel="noopener">{title}</a>'
        else:
            title_html = f'<span class="pub-title">{title}</span>'
        names = ", ".join(
            f"<strong>{html.escape(a)}</strong>" if a in SELF_NAMES else html.escape(a) for a in p["authors"])
        meta = f"<em>{html.escape(p['venue'])}</em>" if p["venue"] else ""
        tail = ", ".join(html.escape(d) for d in p["details"] + [p["year"]] if d)
        meta = ", ".join(x for x in [meta, tail] if x)
        status = "" if p["type"] == "preprint" else \
            '<span class="pub-tag tag-published"><i class="fa-solid fa-circle-check"></i> Published</span>'
        scholar = "https://scholar.google.com/scholar?q=" + re.sub(r"\s+", "+", html.escape(p["title"]))
        link = (f'<a class="pub-action" href="{html.escape(p["url"])}" target="_blank" rel="noopener"><i class="fa-solid fa-arrow-up-right-from-square"></i> View</a>'
                if p["url"] else
                f'<a class="pub-action" href="{scholar}" target="_blank" rel="noopener"><i class="fa-solid fa-magnifying-glass"></i> Find on Scholar</a>')
        out.append(f'''                <article class="selected-publication {cls}" id="{p['key']}">
                    {title_html}
                    <div class="pub-meta">{names}</div>
                    <div class="pub-meta">{meta}</div>
                    <div class="pub-footer">
                        <div class="pub-tags">
                            <span class="pub-tag {tag}"><i class="fa-solid {icon}"></i> {label}</span>
                            {status}
                        </div>
                        <div class="pub-actions">
                            {link}
                            <details class="pub-bib">
                                <summary class="pub-action"><i class="fa-solid fa-quote-right"></i> BibTeX</summary>
                                <pre>{html.escape(p["raw"])}</pre>
                            </details>
                        </div>
                    </div>
                </article>
''')
    return "".join(out)


def replace_between(text, start, end, new):
    i, j = text.index(start) + len(start), text.index(end)
    return text[:i] + new + text[j:]


def main():
    pubs = build()

    page = ROOT / "publications.html"
    s = page.read_text(encoding="utf-8")
    s = replace_between(s, "<!-- PUBLICATIONS:START -->", "<!-- PUBLICATIONS:END -->",
                        render_html(pubs) + "                ")
    page.write_text(s, encoding="utf-8")

    data = [{
        "key": p["key"], "type": p["type"], "title": p["title"],
        "authors": ", ".join(p["authors"]), "year": p["year"], "journal": p["venue"],
        "publisher": next((d for d in p["details"] if not d.startswith(("pp.", "p.", "Art.", "Vol."))), ""),
        "url": p["url"] or "",
    } for p in pubs]
    js = ROOT / "script.js"
    s = js.read_text(encoding="utf-8")
    s = replace_between(s, "/* PUBLICATIONS:START (generated by tools/build_publications.py) */\n",
                        "/* PUBLICATIONS:END */",
                        "window.publications = " + json.dumps(data, indent=4, ensure_ascii=False) + ";\n")
    js.write_text(s, encoding="utf-8")
    counts = {t: sum(1 for p in pubs if p["type"] == t) for t in TYPE_ORDER}
    print(f"{len(pubs)} publications written", counts)


if __name__ == "__main__":
    main()
