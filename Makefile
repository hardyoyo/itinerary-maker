DATA ?= itinerary.yml
export ITINERARY_DATA := $(DATA)

# Monthly evening sky map from Skymaps.com, named after its YYMM date code.
SKYMAP_URL = https://www.skymaps.com/skymaps/tesmn$(shell date +%y%m).pdf
SKYMAP_FILE = skymap-$(shell date +%y%m).pdf

.PHONY: help init install doctor preview render pdf skymap clean clean-cache

.DEFAULT_GOAL := help

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

init: ## Create or edit an itinerary data file (interactively)
	python scripts/init_itinerary.py --output $(DATA)

install: ## Install Python dependencies
	pip install -r requirements.txt

doctor: ## Verify Quarto installation (install, versions, info)
	quarto check install
	quarto check versions
	quarto check info

preview: ## Open live-reload preview in browser
	quarto preview itinerary.qmd

render: ## Render itinerary to static HTML in _site/
	quarto render itinerary.qmd

pdf: ## Render itinerary to PDF in _site/
	quarto render itinerary.qmd --to pdf

skymap: ## Download this month's Skymaps.com evening sky map (PDF)
	@test -f $(SKYMAP_FILE) || curl -fsSL $(SKYMAP_URL) -o $(SKYMAP_FILE)
	@echo "Skymap: $(SKYMAP_FILE)"

clean: clean-cache ## Remove generated output and the Quarto project cache
	rm -rf _site _generated-metadata.yml _generated-resources.md resource-images
	rm -f skymap-*.pdf

clean-cache: ## Remove the Quarto project cache
	rm -rf .quarto/project-cache
