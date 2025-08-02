.PHONY: help install test lint format clean docs build upload

help:  ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install the package in development mode
	bash setup.sh

test:  ## Run the test suite
	pytest

test-cov:  ## Run tests with coverage
	pytest --cov=financial_planner --cov-report=html --cov-report=term

lint:  ## Run linting checks
	flake8 src/ tests/
	mypy src/

format:  ## Format code
	black src/ tests/
	isort src/ tests/

format-check:  ## Check if code is formatted correctly
	black --check src/ tests/
	isort --check-only src/ tests/

clean:  ## Clean up build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

docs:  ## Build documentation
	cd docs && make html

build:  ## Build the package
	python -m build

upload-test:  ## Upload to test PyPI
	python -m twine upload --repository testpypi dist/*

upload:  ## Upload to PyPI
	python -m twine upload dist/*

app:  ## Run the Streamlit app
	streamlit run streamlit_app.py

cli-example:  ## Run a CLI example
	planwise --current-age 30 --retirement-age 67 --salary 40000 --summary

check-all: format-check lint test  ## Run all checks
