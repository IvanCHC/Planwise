# Planwise

A Python library for simulating retirement savings within UK tax wrappers, including Lifetime ISA (LISA), Stocks & Shares ISA, Self-Invested Personal Pension (SIPP), and workplace pensions.

## Features

- **Comprehensive UK Tax Wrappers**: Simulates Lifetime ISA (LISA), Stocks & Shares ISA, Self-Invested Personal Pension (SIPP), and workplace pensions.
- **Accurate Tax Calculations**: Implements UK income tax bands, National Insurance (NI) contributions, and pension tax relief for both Scottish and rest-of-UK regions.
- **Dynamic Contribution Limits**: Adapts to ISA, LISA, and pension annual allowance rules, including age-based restrictions.
- **Flexible Projections**: Supports customizable contribution rates, investment returns, inflation assumptions, and post-retirement analysis.
- **State Pension Integration**: Includes state pension projections based on current UK rules.
- **Rich Visualizations**: Offers interactive charts for contributions and growth using Altair and Plotly.
- **Streamlit App**: Provides an intuitive web interface for pre- and post-retirement analysis.
- **Data-Driven Design**: Utilises JSON-based tax bands, limits, and state pension data for easy updates.
<!-- - **Command Line Interface (CLI)**: Enables quick, non-interactive projections directly from the terminal. -->

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
git clone https://github.com/ivanchc/planwise.git
cd planwise
make install
```

## Quick Start

### Python API

```python
import planwise as pw

```

### Command Line Interface

The `planwise` command provides a quick, non-interactive way to generate a retirement projection from the terminal. Contribution rates can be expressed as fractions of your *take-home salary* (gross salary minus income tax and National Insurance) or as exact amounts. The CLI automatically computes income tax and NI deductions based on the selected tax year and region (Scottish or rest of UK) before applying your contribution percentages. This mirrors the behaviour of the Streamlit app and ensures that allowance checks (LISA limits, ISA allowance, and pension annual allowance) are applied on the same net basis.

Key options include:

| Option | Description |
|--------|-------------|
| `--tax-year` | Tax year for calculations (default: 2025) |
| `--scotland` | Use Scottish tax rates (default: False) |
| `--current-age` | Current age of the individual (default: 25) |
| `--retirement-age` | Retirement age of the individual (default: 67) |
| `--salary` | Annual salary in £ (default: 30,000) |
| `--use-qualifying` | Use qualifying contributions for workplace pensions (default: False) |
| `--workplace-employer-contribution` | Employer contribution rate for workplace pensions (default: 0.03) |
| `--workplace-employee-contribution` | Employee contribution rate for workplace pensions (default: 0.05) |
| `--lisa-contribution` | Lifetime ISA (LISA) contribution rate or amount (default: 0.0) |
| `--isa-contribution` | Stocks & Shares ISA contribution rate or amount (default: 0.0) |
| `--sipp-contribution` | Self-Invested Personal Pension (SIPP) contribution rate or amount (default: 0.0) |
| `--lisa-balance` | Initial balance in LISA (default: 0.0) |
| `--isa-balance` | Initial balance in ISA (default: 0.0) |
| `--sipp-balance` | Initial balance in SIPP (default: 0.0) |
| `--workplace-balance` | Initial balance in workplace pension (default: 0.0) |
| `--roi-lisa` | Annual return on investment for LISA (default: 0.05) |
| `--roi-isa` | Annual return on investment for ISA (default: 0.05) |
| `--roi-sipp` | Annual return on investment for SIPP (default: 0.05) |
| `--roi-workplace` | Annual return on investment for workplace pension (default: 0.05) |
| `--inflation` | Annual inflation rate (default: 0.02) |
| `--summary` | Display a summary of the final pots and growth (default: False) |
| `--output` | Save results to a CSV file (e.g., `results.csv`) |

#### Examples

```bash
# Basic projection using defaults (prints full table)
planwise --current-age 30 --retirement-age 67 --salary 40000

# With custom contribution rates and a summary of the final pots
planwise \
  --current-age 30 \
  --retirement-age 67 \
  --salary 40000 \
  --lisa-contribution 0.05 \
  --isa-contribution 0.10 \
  --sipp-contribution 0.05 \
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
Altair libraries.  They are not installed by default when you
install Planwise.  To enable the plotting API, install the optional
dependencies:

```bash
pip install "planwise[plotting]"

# or for the Streamlit app (includes plotting support)
pip install "planwise[app]"
```

If you attempt to import or call plotting functions without these
dependencies installed you will receive an informative error message.


### Streamlit App

Run the interactive web application:

```bash
make app
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

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This tool is for educational purposes only and does not provide financial advice. Tax rules and allowances may change, so consult a qualified financial adviser for personalised guidance.

Assumptions:
- Tax rules remain constant in nominal terms.
- No carry-forward of unused allowances.
- Pension contributions use the relief-at-source method.
- National Insurance contributions are excluded.
- Growth projections are simplified.
