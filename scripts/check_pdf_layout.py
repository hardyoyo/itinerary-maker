#!/usr/bin/env python3
"""Verify that a rendered PDF uses the condensed gutter-agenda layout.

The PDF render branches on format: the agenda should be the two-column
"gutter" table (date/weekday on the left, details on the right), not the wide
HTML itinerary table. A stale Quarto cache has silently swapped those before,
so this checks the actual PDF text rather than trusting the render.

Usage:
    check_pdf_layout.py <data-file.yml> <itinerary.pdf>
"""

import argparse
import datetime
import re
import shutil
import subprocess
import sys
from pathlib import Path

import yaml


def _pdf_text(pdf_path, pdftotext):
    try:
        return subprocess.run(
            [pdftotext, "-layout", str(pdf_path), "-"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    except subprocess.CalledProcessError as exc:
        sys.exit(f"error: pdftotext failed on {pdf_path}: {exc.stderr.strip()}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data_file", type=Path, help="trip YAML used for the render")
    parser.add_argument("pdf", type=Path, help="rendered PDF to inspect")
    args = parser.parse_args()

    if not args.pdf.exists():
        sys.exit(f"error: PDF not found: {args.pdf}")
    pdftotext = shutil.which("pdftotext")
    if not pdftotext:
        sys.exit("error: pdftotext is required (install poppler-utils)")

    data = yaml.safe_load(args.data_file.read_text()) or {}
    stops = data.get("stops") or []
    if not stops:
        sys.exit(f"error: no stops in {args.data_file}")

    text = _pdf_text(args.pdf, pdftotext)
    failures = []

    for stop in stops:
        try:
            day = datetime.date.fromisoformat(str(stop["date"]))
        except (KeyError, ValueError, TypeError):
            continue
        gutter_date = f"{day.month}/{day.day}"
        weekday = day.strftime("%a").upper()

        if not re.search(rf"(?m)^\s*{re.escape(gutter_date)}(?:\s|$)", text):
            failures.append(f"missing gutter date {gutter_date!r}")
        if not re.search(rf"(?m)^\s*{weekday}\b", text):
            failures.append(f"missing gutter weekday {weekday!r} for {gutter_date}")

    # The wide HTML table labels its columns this way and uses ISO dates in the
    # first cell; the gutter agenda uses "Stay:" and M/D dates instead.
    if "Accommodation" in text:
        failures.append(
            "found the wide table's 'Accommodation' column "
            "(PDF rendered the HTML layout)"
        )

    for heading in ("Route Map", "Trip overview", "Calendar & Weather"):
        if heading not in text:
            failures.append(f"missing section {heading!r}")
    if (data.get("gaps") or "").strip() and "Gaps & open items" not in text:
        failures.append("missing section 'Gaps & open items'")

    if failures:
        print("PDF layout check FAILED:", file=sys.stderr)
        for failure in failures:
            print(f"  - {failure}", file=sys.stderr)
        sys.exit(1)

    print(f"PDF layout check passed ({len(stops)} gutter days, sections present).")


if __name__ == "__main__":
    main()
