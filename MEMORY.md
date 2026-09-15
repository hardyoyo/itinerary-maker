# Project Memory — itinerary-maker

Save this context for revisiting the layout-condensing work.

## Goal (COMPLETED)
Condense the PDF layout to match the reference document `NovaScotiaTrip2024.pdf`
(a printed Google Sheets trip agenda). That goal is done; this records what the
layout now is and the gotchas hit along the way.

## Current verified state (clean, both formats working)
- `quarto render itinerary.qmd` → HTML; `quarto render itinerary.qmd --to pdf` → PDF.
- `make render` (HTML), `make pdf` (PDF), `make skymap`, `make init`, `make clean`.
- **PDF page layout right now (PR trip, 7 stops):**
  - Page 1: title + description + **condensed 2-column "gutter agenda"**. Each
    stop is one row: narrow left column = date (`3/14`) + weekday (`SAT`), wide
    right column = location (bold) + Transport/Stay lines + `•` activity bullets
    + resource links. Days flow continuously; all 7 fit page 1.
  - Page 2: single column — **full-width route map** (Figure 1 caption), then
    the calendar with a bare month header (e.g. "**March 2026**", no section
    heading, no "itinerary dates in bold" note), then a **Weather** heading +
    forecast.
  - Pages 3+: Night Sky Map (`\includepdf{skymap-YYMM.pdf}`) + any resource images.
  - Running header with the trip name (`fancyhdr`, small, centered) + centered
    page-number footer on every page, like the Nova Scotia example.
- **HTML:** unchanged — full-width `.itinerary-table` (6 columns), interactive
  Folium map under "Route Map", Calendar & Forecast section near the end.

## Cross-session decisions that MUST stay
- Agenda layout matches `NovaScotiaTrip2024.pdf`: gutter date+weekday column on
  the left, one day per row, days flow across pages, map/calendar/weather +
  resources appended AFTER the agenda (user chose "append, keep the example look").
- The agenda is only for PDF. HTML keeps its wide table + interactive map.
- The map/calendar/weather block on PDF page 2 is single-column (the earlier
  `layout-ncol` two-column split was removed on request): full-width route map,
  bare "March 2026" calendar header (no "Calendar" heading, no "itinerary dates
  in bold" note), then "### Weather" + forecast. The `_md_calendar()` helper
  takes `with_note=` (True for HTML, False for `calendar_pdf_md`).
- A `<colgroup>` with `<col style="width:12%">`/`<col style="width:88%">` is
  needed on the agenda table — without it pandoc makes both longtable columns
  equal width (the dates column took half the page).
- The agenda table is built as an **HTML `<table>` via `display(HTML(...))`**
  (the reliable pandoc→longtable route), one row per stop.
- `\def\fps@figure{H}` **is now in `_quarto.yml`** header-includes — this is the
  key fix for PDF float scattering. The outer `layout-ncol` figure is emitted by
  Quarto as a bare `\begin{figure}` (default `tbp`) and used to drift to the
  last page. MUST be wrapped in `\makeatletter` / `\makeatother` (the macro name
  contains `@`, and Quarto only turns on `\makeatletter` AFTER header-includes
  run — a bare `\def\fps@figure{H}` silently defines the wrong token and does
  nothing).
- Calendar uses `cal` (fallback `busybox cal`, then Python stdlib `calendar`);
  ANSI stripped. Trip dates bolded.
- Weather via `api.open-meteo.com/v1/forecast` (no key), `forecast_days=16`,
  first stop's lat/lon; WMO-code labels; fallback text "*No forecast yet —
  Open-Meteo covers the next 16 days from today.*" beyond window.
- `_target_format()` (reads `QUARTO_EXECUTE_INFO` env → `"pdf"`/`"html"`) is
  defined ONCE in the first cell of `itinerary.qmd` so the itinerary cell (which
  runs early) can branch on it. Calendar & Forecast and Resources cells reuse it.
- PDF fonts: `mainfont: Source Code Pro` (whole doc), trip **title in Oswald**,
  agenda gutter dates **18pt SCP**, gutter weekdays **10pt SCP**. Fonts are
  installed user-space (no sudo) in `~/.local/share/fonts/`: SourceCodePro
  Regular/Bold/Medium (static TTFs) + Oswald-VF.ttf (variable); `fc-cache`ed.
  The running body font is now SCP, NOT Lato.
  - Title font is set by redefining `\@maketitle` in `_quarto.yml`
    header-includes (`\newfontfamily\quartotitlefont{Oswald}` then a copy of
    article's `\@maketitle` with `\quartotitlefont` inserted). Must be wrapped
    in `\makeatletter`/`\makeatother`.
  - The 18pt/10pt gutter sizes come from `scripts/fontsize-filter.lua` (a Quarto
    `filters:` entry under `format: pdf`): it reads `font-size:Npt` CSS on `<span>`
    (pandoc preserves the `style` attr on Spans) and emits
    `{\fontsize{N}{1.2N}\selectfont ...}`. Filter function must return a FLAT
    list of `Inline`s (a literal Lua table `{open, ...content..., close}`) — do
    NOT use `pandoc.List` methods (no `.append` in quarto's pandoc Lua env) and
    NOT put `el.content` (an `Inlines` sequence, not an `Inline`) inside a list.
  - First LuaLaTeX pass logs `Font "Oswald" not found` while luaotfload
    re-indexes the new font — it resolves on pass 2; not an error.
  - Verify embedded fonts with `pdffonts itinerary.pdf` (expect Oswald-Regular +
    SourceCodePro Regular/Bold/It).
- **Type sizes in the agenda gutter:** date `font-size:18pt`, weekday
  `font-size:10pt`, and the city/location name `font-size:18pt` **regular**
  (no bold). Location is now 18pt (was 16pt) — the date and location are the
  18pt font so their glyph TOPS align naturally (at different sizes the taller
  18pt ascenders poke ~1.4pt above a 16pt neighbour when baselines align).
  All go through `fontsize-filter.lua` → LaTeX `\fontsize`.
- **Subtitle is centered in the PDF** by `scripts/center-subtitle.lua` (takes
  the first paragraph that is a lone `Emph` — the italic description — and
  rewrites it as `\begin{center}\emph{...}` for latex only; HTML untouched).
- **Title** is `\resizebox{\textwidth}{!}{\mbox{\quartotitlefont\@title}}` inside
  the redefined `\@maketitle` — the box fills the full text width. `\mbox` is
  required: without it LaTeX line-breaks the (too-wide) title BEFORE it's scaled
  and you get a wrapped two-line title. Gap to the description is exactly
  `\vskip 1em`; the earlier "huge gap" came from the `\@maketitle` copy still
  rendering empty author/date blocks + `\begin{center}` (a `trivlist` that adds
  its own `\topsep`) — stripped center AND author/date.
- **No horizontal rules in the agenda at all.** Pandoc always emits
  `\bottomrule` for tables; `scripts/agenda-lines.lua` replaces the 2-column
  Table with a bare `longtable` that drops `\toprule` as well as
  `\bottomrule`/`\endlastfoot`. Also removed the markdown `---` that sat between
  the agenda cell and `## Route Map` (it rendered as
  `\rule{0.5\linewidth}{0.5pt}` → the second line).
- geometry 0.5in (was 0.7in — the extra room is what lets all 7 days fit page 1);
  fontsize 10pt; compact tables in
  `_quarto.yml` header-includes (`\AtBeginEnvironment{longtable/tabular}{\small}`,
  `\tabcolsep 4pt`, `\arraystretch 0.8`).
- `make pdf` builds into `/tmp/itinerary-pdf-build` via `--output-dir` then
  `install`s into `_site/` — the old PDF stays openable/readable during the
  render. Mind the alternative: Quarto wipes the output dir at build start.
- Split-stops are normal files (committed); `skymap-*.pdf`, `_site/`,
  `_generated-*`, `_generated-pdf-preamble.tex`, `resource-images/`, `trips/`,
  `.quarto/` are gitignored.
- `_generated-pdf-preamble.tex` is written by `scripts/pre-render.py` with the
  data file's trip name (LaTeX-escaped) for the `fancyhdr` running header; it is
  included via `include-in-header` in `_quarto.yml`.

## Gotchas hit while building the agenda (do not repeat)
1. **HTML-table f-string bug.** The agenda `<style>`/`<table>` was built with a
   plain (non-f) string, so `{_agenda_rows}` stayed literal → the whole table
   was a 534-byte stub → Quarto warned "Unable to parse table from raw html
   block: skipping" and the itinerary vanished from the PDF. Fix: concatenate a
   plain style string with the interpolated `<tbody>`, or escape CSS braces in
   an f-string.
2. **Invalid nested HTML.** `<strong>3/14<br><strong>SAT</strong></strong>`
   (a `<strong>` inside a `<strong>`) can confuse pandoc's HTML reader → table
   skipped. Emit each bold span separately.
3. **`\def\fps@figure{H}` needs `\makeatletter`** (see decisions above).
4. **layout-ncol = floating figure.** The map‖calendar block is a `\begin{figure}`
   (bare = `tbp`); without `\fps@figure{H}` it floats to the END of the document
   (skymap `\includepdf` pages jump ahead of it). `\fps@figure{H}` pins it right
   after the agenda.
5. **skymap is 2 pages**, not 4 — page-count expectations should use
   `pdfinfo ... | grep Pages`, not `pdftotext | awk '/\f/...'` (awk over-counts).
6. **Pandoc Lua table API** (this pandoc/quarto version):
   - `tbl.colspecs[i]` is a plain `{alignment, width}` pair where `width` is the
     raw NUMBER (0.12), not a ColWidth element — don't `colspec[2].c`.
   - Rows are `body.body` (a `Row` per row); cells = `row.cells`; a cell's
     contents = `cell.contents` (Blocks). Serialize a cell faithfully with
     `pandoc.write(pandoc.Pandoc(cell.contents), "latex")` — matches pandoc's
     own longtable output exactly (incl. `\strut` for nbsp bullets). Pandoc's
     longtable writer additionally appends a trailing `\strut` to every
     minipage-wrapped cell, which the standalone write does NOT — add it.
   - `pandoc.List` has no `.append` here; return flat Lua tables
     `{inline, ..., inline}` from element filters.
7. **`\resizebox` on a title wraps** — see title bullet above (`\mbox` fix).
8. **Row gaps in the longtable** — `\\[\d(dim)]` is silently eaten; the only
   spacing that survives is `\noalign{\vskip 9pt}` inserted between rows in
   `agenda-lines.lua` (rows joined with `\\\\\n\noalign{\vskip 9pt}` + trailing
   `\\`, so there is no gap after the last row). 9pt is what still lets row 7
   sit on page 1.

## Test commands (verified to reproduce)
- Render + count pages: `make pdf` then `pdfinfo _site/itinerary.pdf | grep Pages`.
- Secondary data: `ITINERARY_DATA=trips/camping-september-2026.yml quarto render itinerary.qmd --to pdf`.
- HTML unchanged: `quarto render itinerary.qmd` and re-check the `.itinerary-table`.
- PDF integrity when in doubt: `pdftotext -layout _site/itinerary.pdf -` and look
  for the gutter dates (e.g. `3/14` + `SAT`) and the "Route Map"/"Calendar" blocks
  on page 2. `gs -dNOPAUSE -dBATCH -dPDFSTOPONERROR -sDEVICE=nullpage _site/itinerary.pdf`.
- A stale stuck `evince` window can show "Failed to Reload: Timeout" even though
  the file is fine — `killall evince evinced` then reopen.

## Existing git state
- HEAD `00fb5ac5b` "Add optional skymap fetch, trip-level map zoom, and resource
  image embedding". Working tree has uncommitted edits: the agenda layout in
  `itinerary.qmd`, fancyhdr preamble + resource/skymap markers in
  `scripts/pre-render.py`, `\fps@figure{H}` + preamble include in `_quarto.yml`,
  `README.md` (layout description), and `NovaScotiaTrip2024.pdf` (reference,
  untracked) + `MEMORY.md` (untracked).

## Next-session plan (if revisiting layout)
1. The agenda + fancyhdr + float-pin + fonts are stable across PR (4 pages) and
   camping (`trips/camping-september-2026.yml`, 5 pages, 3 stops + images/skymap).
   Any further tweaks would be cosmetic:
   e.g. per-day sub-columns (nested flight/parking columns like the example) —
   note the example nests a second column inside each day's right cell.
2. Keep the HTML branch as-is unless the user asks for a matching condensed
   table in HTML too.
3. Fonts are installed locally (not part of the repo). On a fresh machine run
   `make init`/`make doctor` and re-run the font install (see steps in
   ~/.config notes or the summary: fetch SourceCodePro static TTFs + Oswald VF
   into `~/.local/share/fonts/`, then `fc-cache -f`). If Oswald is replaced,
   remember the variable-font `\bfseries` lookup depends on fontconfig exposing
   a Bold instance.