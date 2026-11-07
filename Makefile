DATA ?= itinerary.yml
export ITINERARY_DATA := $(DATA)

# Monthly evening sky map from Skymaps.com, named after its YYMM date code.
# Default to the current month; set MONTH=YYMM to fetch a trip's month instead.
MONTH ?= $(shell date +%y%m)
SKYMAP_URL = https://www.skymaps.com/skymaps/tesmn$(MONTH).pdf
SKYMAP_FILE = skymap-$(MONTH).pdf

# Quarto executes through a shared transient itinerary.quarto_ipynb. Two
# renders at once race over it and can swap the HTML/PDF output, so serialize
# the render targets rather than trusting everyone to run them one at a time.
RENDER_LOCK = .quarto/render.lock

# Quarto keys its execution cache to itinerary.qmd, not to ITINERARY_DATA or
# the output format. Switching trips or formats (or rendering while a preview
# is open) can therefore reuse the other format's cached cells and swap the
# PDF's gutter agenda for the wide HTML table. Clear it before every render.
CACHE_PATHS = .quarto/project-cache .quarto/_freeze
CLEAR_CACHE = rm -rf $(CACHE_PATHS) && rm -f *.quarto_ipynb
PREVIEW_RUNNING = pgrep -f '[q]uarto preview' >/dev/null

# Overridable so the layout test can render somewhere other than _site.
PDF_BUILD_DIR ?= /tmp/itinerary-pdf-build
PDF_OUT ?= _site/itinerary.pdf

EPUB_BUILD_DIR ?= /tmp/itinerary-epub-build
EPUB_OUT ?= _site/itinerary.epub

.PHONY: help init install hooks doctor preview render pdf epub test skymap clean clean-cache

.DEFAULT_GOAL := help

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

init: ## Create or edit an itinerary data file (interactively)
	python scripts/init_itinerary.py --output $(DATA)

install: ## Install Python dependencies
	pip install -r requirements.txt

hooks: ## Enable the tracked Git pre-commit hook
	git config core.hooksPath .githooks

doctor: ## Verify Quarto installation (install, versions, info)
	quarto check install
	quarto check versions
	quarto check info

preview: ## Open live-reload preview in browser
	quarto preview itinerary.qmd

render: ## Render itinerary to static HTML in _site/
	@mkdir -p .quarto
	@if $(PREVIEW_RUNNING); then \
		echo "error: stop the live preview before rendering — it races over the shared notebook" >&2; \
		exit 1; \
	fi
	flock $(RENDER_LOCK) sh -c '\
		$(CLEAR_CACHE) && \
		quarto render itinerary.qmd'

pdf: ## Render itinerary to PDF in _site/
	# Build into a temporary directory first, then move the finished PDF
	# into place so the previous file stays readable/openable while
	# rendering (Quarto wipes the output dir at the start of a build).
	@mkdir -p .quarto $(dir $(PDF_OUT))
	@if $(PREVIEW_RUNNING); then \
		echo "error: stop the live preview before rendering — it races over the shared notebook" >&2; \
		exit 1; \
	fi
	flock $(RENDER_LOCK) sh -c '\
		$(CLEAR_CACHE) && \
		rm -rf $(PDF_BUILD_DIR) && \
		quarto render itinerary.qmd --to pdf --output-dir $(PDF_BUILD_DIR) && \
		install -m 644 $(PDF_BUILD_DIR)/itinerary.pdf $(PDF_OUT)'
	@echo "PDF ready: $(PDF_OUT)"

epub: ## Render itinerary to EPUB (Pandoc) in _site/
	@mkdir -p .quarto $(dir $(EPUB_OUT))
	@if $(PREVIEW_RUNNING); then \
		echo "error: stop the live preview before rendering — it races over the shared notebook" >&2; \
		exit 1; \
	fi
	flock $(RENDER_LOCK) sh -c '\
		$(CLEAR_CACHE) && \
		rm -rf $(EPUB_BUILD_DIR) && \
		quarto render itinerary.qmd --to epub --output-dir $(EPUB_BUILD_DIR) && \
		install -m 644 $(EPUB_BUILD_DIR)/itinerary.epub $(EPUB_OUT)'
	@echo "EPUB ready: $(EPUB_OUT)"

test: ## Verify the PDF renders in the gutter-agenda layout
	@$(MAKE) --no-print-directory pdf \
		DATA=tests/fixtures/gutter-trip.yml \
		PDF_BUILD_DIR=/tmp/itinerary-test-build \
		PDF_OUT=/tmp/itinerary-test.pdf
	python scripts/check_pdf_layout.py tests/fixtures/gutter-trip.yml /tmp/itinerary-test.pdf

skymap: ## Fetch a month's evening sky map (default: current; set MONTH=YYMM)
	@test -f $(SKYMAP_FILE) || curl -fsSL $(SKYMAP_URL) -o $(SKYMAP_FILE)
	@echo "Skymap: $(SKYMAP_FILE)"

clean: clean-cache ## Remove generated output and the Quarto project cache
	rm -rf _site _generated-metadata.yml _generated-resources.md resource-images
	rm -f skymap-*.pdf

clean-cache: ## Remove the Quarto project cache
	$(CLEAR_CACHE)
