# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Nothing

### Changed
- Nothing

### Deprecated
- Nothing

### Removed
- Nothing

### Fixed
- Nothing

### Security
- Nothing

## [0.2.0] - 2025-08-09

### Added
- Pre-commit configuration for code quality
- Makefile for common development tasks
- Project packaging with `pyproject.toml` and `setup.sh`
- Expanded documentation (`docs/index.md`)
- New CLI entry point (`src/planwise/cli.py`)
- Core logic modules: `core.py`, `ni.py`, `tax.py`, `plotting.py`
- Data files for tax, NI, and pension bands
- Comprehensive test suite for CLI, core, NI, plotting, and tax modules
- Streamlit app (`streamlit_app.py`)

### Changed
- Updated `.gitignore` and `LICENSE`
- Improved `README.md` with new instructions

## [0.1.0] - 2025-08-02

### Added
- Initial release of the Planwise library
- Core projection engine for UK retirement planning
- Support for multiple tax wrappers (LISA, ISA, SIPP, workplace pension)
- Tax relief calculations for both Scottish and rest-of-UK systems
- Age-based contribution rules (e.g., LISA eligibility until age 50)
- Inflation indexing of salaries and contributions
- Contribution limit enforcement (ISA allowance, pension annual allowance)
- Command-line interface for batch processing
- Interactive Streamlit web application
- Plotting functions for visualization
- Comprehensive test coverage
- Full documentation and examples
