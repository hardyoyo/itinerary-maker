# Itinerary Maker

A Quarto project that generates a styled, multi-page travel itinerary from a YAML data file, with an interactive Folium map on the web and a static route map embedded in the PDF.

## Project Structure

```
itinerary-maker/
├── Makefile           # Init / install / preview / render / clean
├── _quarto.yml        # Quarto website configuration
├── epub.css           # Reflowable EPUB styling for the gutter agenda
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
| `make hooks`   | Enable the tracked Git pre-commit hook            |
| `make preview` | Open live-reload preview in the browser           |
| `make render`  | Render itinerary to static HTML in `_site/`       |
| `make pdf`     | Render itinerary to PDF in `_site/`               |
| `make epub`    | Render itinerary to EPUB in `_site/`              |
| `make test`    | Render a fixture and verify the PDF gutter agenda |
| `make skymap`  | Fetch this month's sky map from Skymaps.com (PDF) |
| `make clean`   | Remove generated output                           |

Or call the tools directly:

```bash
quarto preview itinerary.qmd   # live preview
quarto render itinerary.qmd    # static output in _site/
```

`make render` and `make pdf` clear Quarto's execution cache before each build
and refuse to run while a live preview is active, so switching trips or formats
cannot reuse another render's cached cell output. Stop any running preview
first; call `make clean-cache` directly if you only want to drop the cache.

`make epub DATA=trips/<trip>.yml` renders the same itinerary to
`_site/itinerary.epub` through Quarto's Pandoc EPUB writer, so it keeps the PDF's
two-column gutter agenda (with relative font sizes so it reflows on e-readers).
The route map, resource images, overview, booking items, gaps, calendar, and
weather all carry over; sky maps are PDF-only and stay out of the EPUB. Use
`EPUB_OUT=...` to write somewhere other than `_site/` (for example to keep
multiple trips side by side).

`make test` renders `tests/fixtures/gutter-trip.yml` to a temporary PDF and
checks the extracted text for the gutter layout (M/D dates, weekday lines, no
wide-table `Accommodation` column) plus the map/overview/calendar/gaps sections.
It requires `pdftotext` from poppler-utils and network access for map tiles.

Run `make hooks` once per clone to enable the tracked `.githooks/pre-commit`
hook. It rejects every staged file under `trips/` — data, PDF, and HTML alike —
so itineraries containing ticket or booking details cannot be committed even
if force-added. The hook can still be bypassed with `git commit --no-verify`.

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

Optional top-level keys keep trip-specific extras out of the template:

| Key          | Type   | Description                                              |
|--------------|--------|----------------------------------------------------------|
| `overview`   | string | Curated markdown summary rendered under "Trip overview"  |
| `gaps`       | string | Path to a plain-text open-items file, rendered in the PDF (resolved relative to the data file) |
| `skymap`     | bool   | Set `false` to leave the night sky map out of the PDF (default `true`) |
| `trip.temperature_unit` | string | `fahrenheit` (default) or `celsius` for the forecast |

Resources with an `image` URL are fetched into `resource-images/` by the
pre-render script and appended as full-width pictures at the end of both the
HTML and PDF output. Delete `resource-images/` (or `make clean`) to re-download
a refreshed copy.

`make skymap` downloads Skymaps.com's evening sky map to `skymap-YYMM.pdf`,
defaulting to the current month; set `MONTH=YYMM` (e.g. `MONTH=2611`) to fetch
a specific trip month. The PDF build auto-discovers every `skymap-*.pdf` in the
project and appends each one whose month falls inside the trip as its own page
in the resources section (HTML output ignores them) — so you don't need to pass
`MONTH` to both commands. A stray map from an unrelated month is skipped.
Set `skymap: false` in the data file to omit the sky map even when a matching
file exists. Deleting the file(s) (`make clean`) drops them from the next build.

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
shares the following page with the calendar and weather. A footer is added to
every page showing the print date/time, page number, and trip name:

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
