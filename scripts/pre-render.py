#!/usr/bin/env python3
"""Generate document metadata from the itinerary data file before rendering.

Quarto project pre-render script: reads the trip name out of the itinerary
data file (ITINERARY_DATA, defaulting to itinerary.yml) and writes
_generated-metadata.yml, which supplies the document and website title so they
are never hardcoded.
"""

import os
from pathlib import Path

import yaml

DATA_FILE = Path(os.environ.get("ITINERARY_DATA", "itinerary.yml"))
OUTPUT_FILE = Path("_generated-metadata.yml")


def main():
    if not DATA_FILE.exists():
        OUTPUT_FILE.write_text("")
        return
    try:
        data = yaml.safe_load(DATA_FILE.read_text()) or {}
    except yaml.YAMLError:
        OUTPUT_FILE.write_text("")
        return
    name = (data.get("trip") or {}).get("name", "")
    yaml.safe_dump(
        {"title": name, "website": {"title": name}},
        OUTPUT_FILE.open("w"),
        sort_keys=False,
    )
    print(f"Generated {OUTPUT_FILE} with title: {name}")


if __name__ == "__main__":
    main()