.PHONY: help install preview render clean

.DEFAULT_GOAL := help

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

install: ## Install Python dependencies
	pip install -r requirements.txt

preview: ## Open live-reload preview in browser
	quarto preview itinerary.qmd

render: ## Render itinerary to static HTML in _site/
	quarto render itinerary.qmd

clean: ## Remove generated output
	rm -rf _site
