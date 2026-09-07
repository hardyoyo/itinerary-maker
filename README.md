# Itinerary Maker

A Quarto project that generates a styled, multi-page travel itinerary from a YAML data file, with an interactive Folium map.

## Project Structure

```
itinerary-maker/
├── Makefile           # Install / preview / render / clean
├── _quarto.yml        # Quarto website configuration
├── itinerary.yml      # Trip data (stops, dates, activities, coordinates)
├── itinerary.qmd      # Document that renders the itinerary and map
├── requirements.txt   # Python dependencies
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
| `make install` | Install Python dependencies                       |
| `make preview` | Open live-reload preview in the browser           |
| `make render`  | Render itinerary to static HTML in `_site/`       |
| `make clean`   | Remove generated output                           |

Or call the tools directly:

```bash
quarto preview itinerary.qmd   # live preview
quarto render itinerary.qmd    # static output in _site/
```

## Customising the Trip

Edit `itinerary.yml`. Each entry under `stops` follows this schema:

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
