# Planwise

A Python library for modeling retirement savings across various UK tax wrappers including Lifetime ISA (LISA), Stocks & Shares ISA, Self-Invested Personal Pension (SIPP) and workplace pensions.

## Features

- **Comprehensive UK Tax Wrappers**: Models LISA, ISA, SIPP, and workplace pensions
- **Tax Relief Calculations**: Handles pension tax relief for both Scottish and rest-of-UK tax bands
- **Age-based Rules**: Automatically handles LISA contribution limits and age restrictions
- **Flexible Projections**: Customizable contribution rates, returns, and inflation assumptions
- **Rich Visualizations**: Built-in plotting functions using Altair
- **Command Line Interface**: Easy-to-use CLI for quick projections
- **Streamlit App**: Interactive web application for detailed modeling

## Installation

### Using pip

```bash
pip install planwise
```

### Using uv (recommended)

```bash
# Install with core dependencies only
uv pip install planwise

# Install with plotting support
uv pip install "planwise[plotting]"

# Install with Streamlit app support
uv pip install "planwise[app]"

# Install with all dependencies
uv pip install "planwise[all]"
```

### Development Installation

```bash
git clone https://github.com/username/planwise.git
cd planwise
uv pip install -e ".[dev]"
```

## Quick Start

### Python API

```python
import planwise as pw

# Run a basic projection
results = pw.project_retirement(
    current_age=30,
    retirement_age=67,
    salary=40000,
    lisa_contrib_rate=0.05,  # 5% to LISA
    isa_contrib_rate=0.05,   # 5% to ISA
    sipp_employee_rate=0.05, # 5% to SIPP
    sipp_employer_rate=0.0,  # No employer SIPP contributions
    workplace_employee_rate=0.05,  # 5% to workplace pension
    workplace_employer_rate=0.03,  # 3% employer match
    shift_lisa_to_isa=0.5,   # After 50, redirect 50% of LISA to ISA
    shift_lisa_to_sipp=0.5,  # After 50, redirect 50% of LISA to SIPP
    roi_lisa=0.05,           # 5% annual return
    roi_isa=0.05,            # 5% annual return
    roi_sipp=0.05,           # 5% annual return
    roi_workplace=0.05,      # 5% annual return
    inflation=0.02,          # 2% inflation
    scotland=False,          # Use England/Wales/NI tax bands
    use_qualifying_earnings=True,  # Use qualifying earnings for workplace pension
)

print(results.head())
```

### Command Line Interface

```bash
# Basic projection
planwise --current-age 30 --retirement-age 67 --salary 40000

# With custom rates and summary
planwise \
  --current-age 30 \
  --retirement-age 67 \
  --salary 40000 \
  --lisa-rate 0.05 \
  --isa-rate 0.10 \
  --sipp-employee-rate 0.05 \
  --summary

# Save results to CSV
planwise \
  --current-age 30 \
  --retirement-age 67 \
  --salary 40000 \
  --output results.csv

# Use Scottish tax bands
planwise \
  --current-age 30 \
  --retirement-age 67 \
  --salary 40000 \
  --scotland \
  --summary
```

### Plotting

```python
import planwise as pw

# Run projection
results = pw.project_retirement(...)

# Create visualization
contrib_chart = pw.make_contribution_plot(results)
growth_chart = pw.make_growth_plot(results)

# Save charts (requires altair)
contrib_chart.save('contributions.html')
growth_chart.save('growth.html')
```

### Streamlit App

Run the interactive web application:

```bash
streamlit run app.py
```

## Tax Assumptions

The library implements UK tax rules for the 2025/26 tax year:

### Income Tax Bands

**Rest of UK (England, Wales, Northern Ireland):**
- Personal allowance: £12,570
- Basic rate (20%): £12,570 - £50,270
- Higher rate (40%): £50,270 - £125,140
- Additional rate (45%): £125,140+

**Scotland:**
- Personal allowance: £12,570
- Starter rate (19%): £12,570 - £15,397
- Basic rate (20%): £15,397 - £27,491
- Intermediate rate (21%): £27,491 - £43,662
- Higher rate (42%): £43,662 - £75,000
- Advanced rate (45%): £75,000 - £125,140
- Top rate (48%): £125,140+

### Contribution Limits

- **ISA allowance**: £20,000 per year
- **LISA allowance**: £4,000 per year (until age 50), 25% government bonus
- **Pension annual allowance**: £60,000 per year
- **Qualifying earnings**: £6,240 - £50,270 (for auto-enrolment)

### Tax Relief

- Pension contributions receive relief at source (20% basic rate)
- Higher and additional rate taxpayers can claim extra relief
- Scottish taxpayers receive different relief rates due to different tax bands

## Documentation

Full documentation is available at [https://planwise.readthedocs.io](https://planwise.readthedocs.io) (link to be updated).

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This tool is intended for educational purposes and does not constitute financial advice. Tax rules and allowances may change. Users should consult a qualified financial adviser for personalized advice.

The calculations assume:
- Tax rules remain constant in nominal terms
- No carry-forward of unused allowances
- Relief-at-source method for pension contributions
- No consideration of National Insurance contributions
- Simplified growth assumptions

## Development

### Setting up the development environment

```bash
# Clone the repository
git clone https://github.com/ivanchc/planwise.git
cd planwise

# Install development dependencies
uv pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### Running tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=planwise

# Run specific test file
pytest tests/test_core.py
```

### Code formatting

```bash
# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Check types
mypy src/
```

### Building documentation

```bash
cd docs/
make html
```

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a list of changes.
