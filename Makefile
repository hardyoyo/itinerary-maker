.PHONY: help install doctor preview render pdf clean

.DEFAULT_GOAL := help

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

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

clean: ## Remove generated output
	rm -rf _site
