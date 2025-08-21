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

The `planwise` command provides a quick, non-interactive way to generate a
retirement projection from the terminal.  Contribution rates are expressed as
fractions of your *take-home salary* (gross salary minus income tax and
National Insurance).  The CLI automatically computes income tax and NI
deductions based on the selected tax year and region (Scottish or rest of
UK) before applying your contribution percentages.  This mirrors the
behaviour of the Streamlit app and ensures that allowance checks (LISA
limits, ISA allowance and pension annual allowance) are applied on the same
net basis.

Key options include:

| Option | Description |
|-------|-------------|
| `--current-age` | Current age of the individual (default: 30) |
| `--retirement-age` | Age at which saving stops and projection ends (default: 67) |
| `--salary` | Gross annual salary in pounds (required) |
| `--lisa-rate` | Fraction of take-home pay contributed to a Lifetime ISA (default: 0.05) |
| `--isa-rate` | Fraction of take-home pay contributed to a Stocks & Shares ISA (default: 0.05) |
| `--sipp-employee-rate` | Employee contribution to a Self-Invested Personal Pension as a fraction of take-home pay (default: 0.05) |
| `--sipp-employer-rate` | Employer contribution to a SIPP as a fraction of take-home pay (default: 0.0) |
| `--workplace-employee-rate` | Employee contribution to the workplace pension (default: 0.05) |
| `--workplace-employer-rate` | Employer contribution to the workplace pension (default: 0.03) |
| `--shift-lisa-to-isa` | After age 50, fraction of the former LISA contribution redirected to the ISA (default: 0.5) |
| `--shift-lisa-to-sipp` | After age 50, fraction of the former LISA contribution redirected to the SIPP (default: 0.5) |
| `--roi-*` | Expected annual return for each wrapper (`--roi-lisa`, `--roi-isa`, `--roi-sipp`, `--roi-workplace`; default 0.05) |
| `--inflation` | Annual inflation assumption (default: 0.02) |
| `--scotland` | Use Scottish income tax bands instead of rest-of-UK |
| `--use-qualifying-earnings` | Calculate workplace contributions on qualifying earnings instead of full salary |
| `--tax-year` | Tax year used for allowances and tax bands (default: latest available) |
| `--summary` | Display a concise summary of the final pot values rather than the full table |
| `--output` | Path to write the full results as a CSV file |
| `--config` | Load CLI arguments from a JSON configuration file (keys match the long-form flag names without dashes) |

#### Examples

```bash
# Basic projection using defaults (prints full table)
planwise --current-age 30 --retirement-age 67 --salary 40000

# With custom rates and a summary of the final pots
planwise \
  --current-age 30 \
  --retirement-age 67 \
  --salary 40000 \
  --lisa-rate 0.05 \
  --isa-rate 0.10 \
  --sipp-employee-rate 0.05 \
  --summary

# Save results to CSV for further analysis
planwise \
  --current-age 30 \
  --retirement-age 67 \
  --salary 40000 \
  --output results.csv

# Use Scottish tax bands and display a summary
planwise \
  --current-age 30 \
  --retirement-age 67 \
  --salary 40000 \
  --scotland \
  --summary

# Load parameters from a JSON file (overrides CLI flags)
planwise --config params.json --summary
```

### Plotting
The plotting functions in Planwise depend on the optional
Altair and Plotly libraries.  They are not installed by default when you
install Planwise.  To enable the plotting API, install the optional
dependencies:

```bash
pip install "planwise[plotting]"

# or for the Streamlit app (includes plotting support)
pip install "planwise[app]"
```

If you attempt to import or call plotting functions without these
dependencies installed you will receive an informative error message.

The preferred way to build charts from your projection results is via the
``RetirementPlotter`` class in the :mod:`planwise.plotting` module.  Create
an instance with your DataFrame and call its methods to obtain Altair charts:

```python
import planwise as pw

# Run a projection
results = pw.project_retirement(...)

# Build charts
plotter = pw.RetirementPlotter(results)
contrib_chart = plotter.contribution_chart()
growth_chart = plotter.growth_chart()

# Save charts (requires altair)
contrib_chart.save('contributions.html')
growth_chart.save('growth.html')
```

For backwards compatibility the functions ``make_contribution_plot`` and
``make_growth_plot`` remain available on the top level of ``planwise.plotting``
and behave identically to the corresponding methods on ``RetirementPlotter``.

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
