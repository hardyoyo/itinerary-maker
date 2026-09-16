# Itinerary Maker

A Quarto project that generates a styled, multi-page travel itinerary from a YAML data file, with an interactive Folium map on the web and a static route map embedded in the PDF.

## Project Structure

```
itinerary-maker/
├── Makefile           # Init / install / preview / render / clean
├── _quarto.yml        # Quarto website configuration
├── itinerary.yml      # Trip data (stops, dates, activities, coordinates)
├── itinerary.qmd      # Document that renders the itinerary and map
├── requirements.txt   # Python dependencies
├── scripts/           # pre-render metadata + interactive init quiz
└── README.md
```

## Prerequisites

- **Python 3.9+**
- **Quarto** — install from <https://quarto.org/docs/get-started/>
- Python packages listed in `requirements.txt`

## Installation

```bash
git clone <repo-url> && cd itinerary-maker
pip install -r requirements.txt
```

## Usage

Run `make help` to list available commands. Common workflows:

| Command        | Action                                            |
|----------------|---------------------------------------------------|
| `make init`    | Create/edit the itinerary data file (interactively)|
| `make install` | Install Python dependencies                       |
| `make preview` | Open live-reload preview in the browser           |
| `make render`  | Render itinerary to static HTML in `_site/`       |
| `make pdf`     | Render itinerary to PDF in `_site/`               |
| `make skymap`  | Fetch this month's sky map from Skymaps.com (PDF) |
| `make clean`   | Remove generated output                           |

Or call the tools directly:

```bash
quarto preview itinerary.qmd   # live preview
quarto render itinerary.qmd    # static output in _site/
```

## Customising the Trip

Run `make init` to create or edit the itinerary data file interactively. It
walks you through the trip name, description, and each stop one field at a
time. If a data file already exists, its values are shown as defaults so a
re-run edits rather than replaces it. Coordinates are looked up automatically
when possible; `--no-geocode` and `--blank` options are available via the
underlying `scripts/init_itinerary.py`.

Or edit `itinerary.yml` directly. Each entry under `stops` follows this schema:

| Field          | Type     | Description                                      |
|----------------|----------|--------------------------------------------------|
| `date`         | string   | ISO date (`YYYY-MM-DD`)                          |
| `location`     | string   | Place name                                       |
| `accommodation`| string   | Hotel, Airbnb, etc.                              |
| `transport`    | object   | `mode` (string) and `notes` (string)             |
| `activities`   | list     | Bullet-point list of planned activities           |
| `resources`    | list     | Optional links: `name`, `url`, and an optional `image` URL that is downloaded and embedded at the end of the document |
| `lat`          | number   | Latitude for the map marker                      |
| `lon`          | number   | Longitude for the map marker                     |

Resources with an `image` URL are fetched into `resource-images/` by the
pre-render script and appended as full-width pictures at the end of both the
HTML and PDF output. Delete `resource-images/` (or `make clean`) to re-download
a refreshed copy.

`make skymap` downloads Skymaps.com's evening sky map to `skymap-YYMM.pdf`,
defaulting to the current month; set `MONTH=YYMM` (e.g. `MONTH=2611`) to fetch
a specific trip month. When a sky map is present, the PDF build appends it as
its own page in the resources section (HTML output ignores it), but only if its
month falls inside the trip dates — the pre-render script matches the
`skymap-YYMM.pdf` filename against the stops' months, so a stray map never
lands in the document. Deleting the file (`make clean`) drops it from the next
build.

An optional `zoom` value under `trip` sets the route-map zoom level: it caps
how far in the auto-fitted PDF map can zoom (so a single-location trip like a
campground still shows the approach roads) and sets the starting zoom of the
interactive web map (default 9). Leave it out to auto-fit every stop.

## Calendar & Weather

Each render adds a compact calendar and a short-range weather forecast so you
can see the trip dates and the expected conditions at a glance. In the HTML
output they sit near the end, just before the resources section.

The **PDF output** is a condensed, document-style layout modeled on a printed
Google Sheets trip agenda: each day is one row — a narrow date + weekday gutter
column on the left and that day's details (transport, stay, activities, links)
on the right — so days flow continuously across pages. The route map then
shares the following page with the calendar and weather, and a running header
with the trip name and a page-number footer are added to every page:

- **Calendar** — every month the trip spans is drawn with the `cal` command
  (falling back to `busybox cal`, then Python's stdlib `calendar` module) and
  the itinerary dates are highlighted on it.
- **Weather** — the first stop's coordinates are sent to the
  [Open-Meteo](https://open-meteo.com/) forecast API (no key required) and a
  per-day high/low + conditions table is emitted for the itinerary dates that
  fall inside its 16-day forecast window. If the trip is further out than that,
  or the render is offline, a short note is shown instead.

Both sections read only the `date` and `lat`/`lon` fields already in the data
file, so no extra configuration is needed.

Add, remove, or reorder stops — the table and map update automatically on the next render.

Nothing is hardcoded: the document title and site title are pulled from the
`trip.name` field of the data file. A Quarto pre-render script
(`scripts/pre-render.py`) reads the file and generates `_generated-metadata.yml`
(git-ignored) just before each render, so `make render` and
`quarto render itinerary.qmd` both pick it up.

## Using a Different Data File

By default the project reads `itinerary.yml`. To render a different file with
`make`, set the `DATA` Make variable:

```bash
make render DATA=work-trip.yml
```

When calling `quarto` directly, pass the `ITINERARY_DATA` environment variable
instead (this is what `DATA` sets under the hood):

```bash
ITINERARY_DATA=work-trip.yml quarto render itinerary.qmd
```

Note that `make` always overrides `ITINERARY_DATA` with the value of `DATA`, so
set `DATA` when going through the Makefile.
