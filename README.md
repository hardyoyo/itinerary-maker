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
| `lat`          | number   | Latitude for the map marker                      |
| `lon`          | number   | Longitude for the map marker                     |

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
