#!/usr/bin/env python3
"""Generate document metadata and resource image assets before rendering.

Quarto project pre-render script. Reads the itinerary data file
(ITINERARY_DATA, defaulting to itinerary.yml) and writes:

* _generated-metadata.yml — the trip name, so the document/website titles are
  never hardcoded.
* resource-images/ — one file per stop resource that carries an `image` URL,
  fetched up front so pictures render in both the HTML and PDF output without
  a live network connection at render time.
* _generated-resources.md — markdown that embeds those images; the document
  emits it from a code cell so it is appended at the end in both HTML and PDF.
  If this month's sky map has been fetched (e.g. `make skymap`), a page
  embedding that PDF is appended to the same file so it lands in the
  resources section of the rendered document.
"""

import datetime
import os
import re
import time
import urllib.request
from pathlib import Path

import yaml

DATA_FILE = Path(os.environ.get("ITINERARY_DATA", "itinerary.yml"))
OUTPUT_FILE = Path("_generated-metadata.yml")
RESOURCES_OUTPUT = Path("_generated-resources.md")
PDF_PREAMBLE_FILE = Path("_generated-pdf-preamble.tex")
IMAGE_DIR = Path("resource-images")
# Named after Skymaps.com's YYMM date code (see the Makefile's skymap target).
SKYMAP_FILE = Path(os.environ.get("SKYMAP_FILE", f"skymap-{time.strftime('%y%m')}.pdf"))

# Some park-district CDNs reject the bare urllib user agent.
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}


def _slugify(name):
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "image"


def _fetch_image(resource):
    """Download the resource image into IMAGE_DIR and return the markdown
    embedding for it, or None if it cannot be retrieved.

    The file is cached under a slug derived from the resource name; delete
    resource-images/ (or `make clean`) to re-download a refreshed copy.
    """
    url = resource["image"]
    suffix = Path(url.split("?")[0]).suffix.lower()
    if suffix not in (".png", ".jpg", ".jpeg", ".gif", ".webp"):
        suffix = ".png"
    local = IMAGE_DIR / f"{_slugify(resource['name'])}{suffix}"
    if not local.exists():
        try:
            request = urllib.request.Request(url, headers=_HEADERS)
            with urllib.request.urlopen(request, timeout=30) as response:
                local.write_bytes(response.read())
        except OSError:
            return None
    caption = resource["name"]
    if resource.get("url"):
        caption = f"[{caption}]({resource['url']})"
    return f"#### {caption}\n\n![{resource['name']}]({local}){{width=100%}}\n\n"


def _latex_escape(text):
    """Escape a string for safe use in LaTeX source (a document title)."""
    return (
        text.replace("\\", r"\textbackslash{}")
        .replace("{", r"\{")
        .replace("}", r"\}")
        .replace("$", r"\$")
        .replace("&", r"\&")
        .replace("#", r"\#")
        .replace("_", r"\_")
        .replace("%", r"\%")
        .replace("^", r"\textasciicircum{}")
        .replace("~", r"\textasciitilde{}")
    )


def _pdf_preamble(title):
    """LaTeX header-include for PDF output: a running page header with the trip
    name and a centered page-number footer, matching the example layout."""
    circled = "\n".join(
        f"\\newunicodechar{{{chr(0x2460 + n - 1)}}}"
        f"{{\\fontspec{{DejaVu Sans}}{chr(0x2460 + n - 1)}}}"
        for n in range(1, 21)
    )
    return (
        "\\usepackage{fancyhdr}\n"
        "\\usepackage{newunicodechar}\n"
        f"{circled}\n"
        "\\pagestyle{fancy}\n"
        "\\fancyhf{}\n"
        f"\\fancyhead[C]{{\\small {_latex_escape(title)} \\strut}}\n"
        "\\fancyfoot[C]{\\thepage}\n"
        "\\renewcommand{\\headrulewidth}{0pt}\n"
    )


def _trip_skymap_months(data):
    """Return the set of YYMM codes spanned by the trip's stop dates.

    Skymaps.com dates its maps by month (yyMM), so the map only belongs in
    the document when one of the trip's months matches. Trips with no dates
    (or an unparseable one) yield an empty set, i.e. no sky map."""
    months = set()
    for stop in data.get("stops") or []:
        date = (stop or {}).get("date")
        if not date:
            continue
        try:
            months.add(datetime.date.fromisoformat(date).strftime("%y%m"))
        except ValueError:
            continue
    return months


def _skymap_block(data):
    """Return markdown embedding the fetched sky map PDF, or None if it has
    not been fetched yet or its month does not fall inside the trip.

    Filenames follow Skymaps.com's YYMM date code (`skymap-YYMM.pdf`); a file
    whose name fits that pattern is included only when its month matches one
    of the trip's months. A differently-named file (the SKYMAP_FILE override)
    is assumed deliberate and always included. The raw LaTeX include only
    takes effect for PDF output, so the whole block is marked pdf-only. No
    heading: the sky map page carries its own title."""
    if not SKYMAP_FILE.exists():
        return None
    months = _trip_skymap_months(data)
    match = re.fullmatch(r"skymap-(\d{4})\.pdf", SKYMAP_FILE.name)
    if match and months and match.group(1) not in months:
        return None
    return (
        '::: {.content-visible when-format="pdf"}\n'
        f"\\includepdf[fitpaper=true,pages=-]{{{SKYMAP_FILE}}}\n"
        ":::\n\n"
    )


def main():
    try:
        data = yaml.safe_load(DATA_FILE.read_text()) or {}
    except (OSError, yaml.YAMLError):
        data = {}

    name = (data.get("trip") or {}).get("name", "")
    yaml.safe_dump(
        {"title": name, "website": {"title": name}},
        OUTPUT_FILE.open("w"),
        sort_keys=False,
    )
    print(f"Generated {OUTPUT_FILE} with title: {name}")

    PDF_PREAMBLE_FILE.write_text(_pdf_preamble(name), encoding="utf-8")
    print(f"Generated {PDF_PREAMBLE_FILE}")

    IMAGE_DIR.mkdir(exist_ok=True)
    blocks = []
    for stop in data.get("stops") or []:
        for resource in stop.get("resources") or []:
            if resource.get("image"):
                block = _fetch_image(resource)
                if block:
                    blocks.append(block)

    sections = []
    if blocks:
        sections.append("## Campground Maps\n\n" + "".join(blocks))
    skymap = _skymap_block(data)
    if skymap:
        sections.append(skymap)
    body = "".join(sections)
    RESOURCES_OUTPUT.write_text(body, encoding="utf-8")
    detail = f" with {len(blocks)} embedded image(s)"
    if skymap:
        detail += f" and the {SKYMAP_FILE.name} sky map"
    print(f"Generated {RESOURCES_OUTPUT}{detail}")


if __name__ == "__main__":
    main()