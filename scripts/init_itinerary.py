#!/usr/bin/env python3
"""Interactively quiz the user and write an itinerary data file (YAML).

Usage:
    python scripts/init_itinerary.py [--output itinerary.yml] [--blank] [--no-geocode]

When --output points at an existing file, its values are shown as defaults so
the script is safe to re-run when editing an itinerary.

Coordinates are looked up automatically with the free Nominatim geocoder when
the place has no stored coordinates yet; use --no-geocode to skip the lookup
offline (you'll then be prompted for them by hand).
"""

import argparse
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

import yaml

GEOCODE_URL = "https://nominatim.openstreetmap.org/search"
MIN_GEOCODE_DELAY = 1.0  # Nominatim usage policy: max 1 request/second
_last_request = [0.0]


def parse_args():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", default="itinerary.yml", help="Itinerary file to create/edit"
    )
    parser.add_argument(
        "--blank",
        action="store_true",
        help="Start from blank prompts instead of loading an existing file",
    )
    parser.add_argument(
        "--no-geocode",
        action="store_true",
        help="Skip the automatic location lookup and ask for coordinates by hand",
    )
    return parser.parse_args()


def geocode(location):
    """Best-effort lat/lon lookup for a place name, or None if it fails."""
    try:
        elapsed = time.time() - _last_request[0]
        if elapsed < MIN_GEOCODE_DELAY:
            time.sleep(MIN_GEOCODE_DELAY - elapsed)
        _last_request[0] = time.time()
        params = urllib.parse.urlencode({"q": location, "format": "json", "limit": 1})
        req = urllib.request.Request(
            GEOCODE_URL + "?" + params,
            headers={"User-Agent": "itinerary-maker-init-script"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            results = json.loads(resp.read().decode())
        if results:
            return float(results[0]["lat"]), float(results[0]["lon"])
    except OSError:
        pass
    return None


def prompt(label, default=None):
    """Ask for one line of input; a blank answer returns the default."""
    suffix = f" [{default}]" if default not in (None, "") else ""
    return input(f"{label}{suffix}: ").strip() or (default or "")


def ask_required(label, default=None):
    while True:
        value = prompt(label, default)
        if value:
            return value
        print("  (this is required)")


def ask_yes_no(label, default=True):
    suffix = " [Y/n]" if default else " [y/N]"
    while True:
        value = input(label + suffix + ": ").strip().lower()
        if value == "":
            return default
        if value in ("y", "yes"):
            return True
        if value in ("n", "no"):
            return False
        print("  (answer yes or no)")


def ask_float(label, default=None):
    """Ask for a number; returns None on a blank answer with no default."""
    while True:
        value = prompt(label, default)
        if value == "":
            return None
        try:
            return float(value)
        except ValueError:
            print("  (enter a number)")


def ask_list(label, existing=None):
    items = list(existing) if existing else []
    collected = []
    n = 1
    while True:
        default = items[n - 1] if n <= len(items) else None
        value = prompt(f"{label} {n}", default)
        if value:
            collected.append(value)
        elif default:
            collected.append(default)
        else:
            return collected
        n += 1


def ask_coordinates(location, default_lat=None, default_lon=None, do_geocode=True):
    lat, lon = default_lat, default_lon
    if (lat is None or lon is None) and do_geocode:
        found = geocode(location)
        if found:
            lat, lon = found
            print(f"  Geocoded '{location}' -> {lat:.4f}, {lon:.4f}")
    lat = ask_float("Latitude", lat)
    lon = ask_float("Longitude", lon)
    if lat is None or lon is None:
        lat, lon = 0.0, 0.0
        print("  (warning: missing coordinates; map markers will fall at 0,0)")
    return lat, lon


def load_existing(path):
    if not path.exists() or path.stat().st_size == 0:
        return {}
    try:
        return yaml.safe_load(path.read_text()) or {}
    except yaml.YAMLError:
        print(f"Note: could not parse {path}; starting from blank prompts.")
        return {}


def main():
    args = parse_args()
    output = Path(args.output)
    old = {} if args.blank else load_existing(output)
    trip = old.get("trip", {})
    stops = old.get("stops") or []

    print("Let's build your itinerary. Press Enter to accept a shown default.")
    print()
    name = ask_required("Trip name", trip.get("name"))
    description = prompt("Trip description", trip.get("description", ""))
    print()

    completed = []
    n = 1
    while True:
        current = stops[n - 1] if n <= len(stops) else None
        if current:
            print(f"--- Stop {n} (updating {current.get('location', '?')})")
        else:
            print(f"--- Stop {n} (leave Date blank to finish)")
        date = prompt("Date (YYYY-MM-DD)", current.get("date") if current else None)
        if not date:
            print()
            break
        location = ask_required("Location", current.get("location") if current else None)
        accommodation = prompt(
            "Accommodation", current.get("accommodation") if current else ""
        )
        transport = (current or {}).get("transport") or {}
        transport_mode = ask_required("Transport mode", transport.get("mode"))
        transport_notes = prompt("Transport notes", transport.get("notes", ""))
        activities = ask_list("Activity", current.get("activities") if current else None)
        lat, lon = ask_coordinates(
            location,
            current.get("lat") if current else None,
            current.get("lon") if current else None,
            do_geocode=not args.no_geocode,
        )
        completed.append(
            {
                "date": date,
                "location": location,
                "accommodation": accommodation,
                "transport": {"mode": transport_mode, "notes": transport_notes},
                "activities": activities,
                "lat": lat,
                "lon": lon,
            }
        )
        print()
        n += 1

    data = {"trip": {"name": name, "description": description}, "stops": completed}

    print("Here is what I'll write:")
    print(yaml.safe_dump(data, sort_keys=False, allow_unicode=True))
    if ask_yes_no(f"Write this to {output}?", default=True):
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(yaml.safe_dump(data, sort_keys=False, allow_unicode=True))
        print(f"Wrote {output}")
    else:
        print("Aborted; nothing was written.")
        raise SystemExit(1)


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nAborted; nothing was written.")
        raise SystemExit(130)