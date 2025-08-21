.PHONY: help install test lint format clean docs build upload

help:  ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Install the package in development mode
	bash setup.sh

test:  ## Run the test suite
	pytest

test-cov:  ## Run tests with coverage
	pytest --cov=planwise --cov-report=html --cov-report=term

lint:  ## Run linting checks
	mypy src/

format:  ## Format code
	black src/ tests/ streamlit_app.py
	isort src/ tests/ streamlit_app.py

clean:  ## Clean up build artifacts
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .profiles/
	find . -type d -name __pycache__ -delete
	find . -type f -name "*.pyc" -delete

docs:  ## Build documentation
	cd docs && make html

app:  ## Run the Streamlit app
	streamlit run streamlit_app.py
