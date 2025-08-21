# Planwise Documentation

A Python library for simulating retirement savings within UK tax wrappers, including Lifetime ISA (LISA), Stocks & Shares ISA, Self-Invested Personal Pension (SIPP), and workplace pensions.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [API Reference](#api-reference)
- [CLI Reference](#cli-reference)
- [Streamlit App](#streamlit-app)
- [Tax Assumptions](#tax-assumptions)
- [Examples](#examples)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)

## Features

- **Comprehensive UK Tax Wrappers**: Simulates Lifetime ISA (LISA), Stocks & Shares ISA, Self-Invested Personal Pension (SIPP), and workplace pensions.
- **Accurate Tax Calculations**: Implements UK income tax bands, National Insurance (NI) contributions, and pension tax relief for both Scottish and rest-of-UK regions.
- **Dynamic Contribution Limits**: Adapts to ISA, LISA, and pension annual allowance rules, including age-based restrictions.
- **Flexible Projections**: Supports customizable contribution rates, investment returns, inflation assumptions, and post-retirement analysis.
- **State Pension Integration**: Includes state pension projections based on current UK rules.
- **Rich Visualizations**: Offers interactive charts for contributions and growth using Altair and Plotly.
- **Streamlit App**: Provides an intuitive web interface for pre- and post-retirement analysis.
- **Data-Driven Design**: Utilises JSON-based tax bands, limits, and state pension data for easy updates.

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

# Create user profile
user = pw.core.UserProfile(
    current_age=30,
    retirement_age=67,
    salary=40000,
    scotland=False,
    account_balances=pw.core.AccountBalances(
        isa_balance=5000,
        lisa_balance=0,
        sipp_balance=0,
        workplace_pension_balance=0
    )
)

# Set contribution rates
contrib = pw.core.ContributionRates(
    lisa=0.05,  # 5% of take-home salary
    isa=0.10,   # 10% of take-home salary
    sipp_employee=0.05,  # 5% employee contribution
    sipp_employer=0.03,  # 3% employer contribution
    workplace_employee=0.05,
    workplace_employer=0.03
)

# Set investment returns
returns = pw.core.InvestmentReturns(
    lisa=0.05,
    isa=0.05,
    sipp=0.05,
    workplace=0.05
)

# Calculate income breakdown
income = pw.core.IncomeBreakdown(
    salary=40000,
    take_home_salary=32000,  # After tax and NI
    ni_due=3000,
    income_tax=5000
)

# Run projection
df = pw.project_retirement(
    user=user,
    contrib=contrib,
    returns=returns,
    income=income,
    inflation=0.02,
    use_qualifying_earnings=False,
    year=2025
)

print(df.head())
```

### Command Line Interface

```bash
# Basic projection
planwise --current-age 30 --retirement-age 67 --salary 40000

# With custom contributions and summary
planwise \
  --current-age 30 \
  --retirement-age 67 \
  --salary 40000 \
  --lisa-contribution 0.05 \
  --isa-contribution 0.10 \
  --summary

# Save to CSV
planwise --salary 40000 --output results.csv
```

### Streamlit App

```bash
# Run the interactive web application
make app

# Or directly with streamlit
streamlit run streamlit_app.py
```

## API Reference

### Core Classes

#### `UserProfile`

Represents a user's basic demographic and financial information.

**Parameters:**
- `current_age` (int): Current age of the user
- `retirement_age` (int): Target retirement age
- `salary` (float): Annual gross salary in £
- `scotland` (bool): Whether to use Scottish tax rates
- `account_balances` (AccountBalances): Initial account balances

#### `ContributionRates`

Defines contribution rates for different investment vehicles.

**Parameters:**
- `lisa` (float): LISA contribution rate (0-1) or absolute amount
- `isa` (float): ISA contribution rate (0-1) or absolute amount
- `sipp_employee` (float): Employee SIPP contribution rate
- `sipp_employer` (float): Employer SIPP contribution rate
- `workplace_employee` (float): Employee workplace pension rate
- `workplace_employer` (float): Employer workplace pension rate
- `shift_lisa_to_isa` (float): Redirect LISA to ISA after age 50
- `shift_lisa_to_sipp` (float): Redirect LISA to SIPP after age 50

#### `InvestmentReturns`

Annual investment return rates for each account type.

**Parameters:**
- `lisa` (float): LISA annual return rate
- `isa` (float): ISA annual return rate
- `sipp` (float): SIPP annual return rate
- `workplace` (float): Workplace pension annual return rate

#### `IncomeBreakdown`

Breakdown of salary components after tax and NI.

**Parameters:**
- `salary` (float): Gross annual salary
- `take_home_salary` (float): Net salary after tax and NI
- `ni_due` (float): National Insurance contributions
- `income_tax` (float): Income tax due

#### `AccountBalances`

Initial balances across different account types.

**Parameters:**
- `isa_balance` (float): Starting ISA balance
- `lisa_balance` (float): Starting LISA balance
- `sipp_balance` (float): Starting SIPP balance
- `workplace_pension_balance` (float): Starting workplace pension balance

### Core Functions

#### `project_retirement()`

Main projection function that calculates retirement savings over time.

```python
def project_retirement(
    user: UserProfile,
    contrib: ContributionRates,
    returns: InvestmentReturns,
    income: IncomeBreakdown,
    inflation: float = 0.02,
    use_qualifying_earnings: bool = False,
    year: int = 2025
) -> pd.DataFrame:
```

**Returns:** DataFrame with yearly projections including contributions, growth, and balances.

#### `calculate_income_tax()`

Calculates income tax based on UK tax bands.

```python
def calculate_income_tax(
    salary: float,
    year: int = 2025,
    scotland: bool = False
) -> float:
```

**Returns:** Annual income tax due in £.

#### `get_tax_bands()`

Retrieves tax bands for a given year and region.

```python
def get_tax_bands(year: int = 2025, scotland: bool = False) -> List[TaxBand]:
```

**Returns:** List of TaxBand objects with rates and thresholds.

### Plotting Functions

#### `make_contribution_plot()`

Creates an Altair chart showing annual contributions by account type.

```python
def make_contribution_plot(df: pd.DataFrame) -> alt.Chart:
```

#### `make_growth_plot()`

Creates an Altair chart showing pot growth over time.

```python
def make_growth_plot(df: pd.DataFrame) -> alt.Chart:
```

#### `make_income_breakdown_pie()`

Creates a Plotly pie chart of income breakdown.

```python
def make_income_breakdown_pie(income: IncomeBreakdown) -> go.Figure:
```

#### `RetirementPlotter`

Class-based interface for creating retirement projection charts.

```python
plotter = pw.RetirementPlotter(df)
contrib_chart = plotter.contribution_chart()
growth_chart = plotter.growth_chart()
```

## CLI Reference

The `planwise` command provides command-line access to the projection engine.

### Basic Usage

```bash
planwise [OPTIONS]
```

### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--tax-year` | int | 2025 | Tax year for calculations |
| `--scotland` | flag | False | Use Scottish tax rates |
| `--current-age` | int | 25 | Current age |
| `--retirement-age` | int | 67 | Retirement age |
| `--salary` | float | 30000 | Annual salary in £ |
| `--use-qualifying` | flag | False | Use qualifying earnings for workplace pensions |
| `--workplace-employer-contribution` | float | 0.03 | Employer workplace pension rate |
| `--workplace-employee-contribution` | float | 0.05 | Employee workplace pension rate |
| `--lisa-contribution` | float | 0.0 | LISA contribution rate/amount |
| `--isa-contribution` | float | 0.0 | ISA contribution rate/amount |
| `--sipp-contribution` | float | 0.0 | SIPP contribution rate/amount |
| `--lisa-balance` | float | 0.0 | Initial LISA balance |
| `--isa-balance` | float | 0.0 | Initial ISA balance |
| `--sipp-balance` | float | 0.0 | Initial SIPP balance |
| `--workplace-balance` | float | 0.0 | Initial workplace pension balance |
| `--roi-lisa` | float | 0.05 | LISA annual return |
| `--roi-isa` | float | 0.05 | ISA annual return |
| `--roi-sipp` | float | 0.05 | SIPP annual return |
| `--roi-workplace` | float | 0.05 | Workplace pension annual return |
| `--inflation` | float | 0.02 | Annual inflation rate |
| `--summary` | flag | False | Show summary statistics |
| `--output` | str | None | Save results to CSV file |
| `--config` | str | None | Load parameters from JSON file |

### Examples

```bash
# Basic projection with defaults
planwise --current-age 30 --retirement-age 67 --salary 40000

# Custom contributions with summary
planwise \
  --current-age 30 \
  --retirement-age 67 \
  --salary 40000 \
  --lisa-contribution 0.05 \
  --isa-contribution 0.10 \
  --sipp-contribution 0.05 \
  --summary

# Scottish tax rates
planwise --salary 40000 --scotland --summary

# Save to file
planwise --salary 40000 --output my_projection.csv

# Load from config file
planwise --config my_profile.json --summary
```

### Configuration Files

You can save parameters in a JSON file:

```json
{
  "current_age": 30,
  "retirement_age": 67,
  "salary": 40000,
  "scotland": false,
  "lisa_contribution": 0.05,
  "isa_contribution": 0.10,
  "sipp_contribution": 0.05,
  "roi_lisa": 0.06,
  "roi_isa": 0.05,
  "roi_sipp": 0.06,
  "inflation": 0.025
}
```

## Streamlit App

The interactive web application provides a user-friendly interface for retirement planning.

### Features

- **Interactive Input Controls**: Sliders and inputs for all parameters
- **Real-time Calculations**: Results update as you change inputs
- **Multiple Visualizations**: Charts for contributions, growth, and breakdowns
- **Pre and Post-Retirement Analysis**: Separate tabs for different life phases
- **Profile Management**: Save and load different scenarios
- **Data Export**: Download results as CSV

### Running the App

```bash
# Using make
make app

# Direct streamlit command
streamlit run streamlit_app.py

# With custom port
streamlit run streamlit_app.py --server.port 8502
```

### App Sections

#### Sidebar Controls

- Personal details (age, salary, location)
- Contribution rates for each account type
- Investment return assumptions
- Post-50 LISA redirection options

#### Pre-Retirement Analysis

- Summary metrics and final pot values
- Salary and contribution breakdown
- Year-by-year projection table
- Interactive charts for contributions and growth
- Data download options

#### Post-Retirement Analysis

- Withdrawal projections
- State pension integration
- Inflation-adjusted spending power
- Longevity analysis

## Tax Assumptions

Planwise implements UK tax rules for the 2025/26 tax year.

### Income Tax Bands

#### Rest of UK (England, Wales, Northern Ireland)

| Band | Rate | Threshold |
|------|------|-----------|
| Personal Allowance | 0% | £0 - £12,570 |
| Basic Rate | 20% | £12,570 - £50,270 |
| Higher Rate | 40% | £50,270 - £125,140 |
| Additional Rate | 45% | £125,140+ |

#### Scotland

| Band | Rate | Threshold |
|------|------|-----------|
| Personal Allowance | 0% | £0 - £12,570 |
| Starter Rate | 19% | £12,570 - £15,397 |
| Basic Rate | 20% | £15,397 - £27,491 |
| Intermediate Rate | 21% | £27,491 - £43,662 |
| Higher Rate | 42% | £43,662 - £75,000 |
| Advanced Rate | 45% | £75,000 - £125,140 |
| Top Rate | 48% | £125,140+ |

### National Insurance Rates

| Category | Rate | Threshold |
|----------|------|-----------|
| Employee Class 1 | 12% | £12,570 - £50,270 |
| Employee Class 1 (Higher) | 2% | £50,270+ |
| Employer Class 1 | 13.8% | £9,100+ |

### Contribution Limits

- **ISA Allowance**: £20,000 per year
- **LISA Allowance**: £4,000 per year (until age 50)
- **LISA Bonus**: 25% government bonus (max £1,000/year)
- **Pension Annual Allowance**: £60,000 per year
- **Qualifying Earnings**: £6,240 - £50,270 (for auto-enrolment)

### Tax Relief

- **Pension Contributions**: Relief at source (20% basic rate)
- **Higher Rate Relief**: Additional relief for higher/additional rate taxpayers
- **Scottish Relief**: Different rates due to different tax bands
- **Employer Contributions**: No limit, fully deductible

### Key Assumptions

- Tax rules remain constant in nominal terms
- No carry-forward of unused allowances
- Pension contributions use relief-at-source method
- LISA eligibility ends at age 50
- State pension starts at age 67 (configurable)
- Growth projections are simplified (no volatility modeling)


## Development

### Setting Up Development Environment

```bash
# Clone repository
git clone https://github.com/ivanchc/planwise.git
cd planwise

# Install in development mode
make install

# Or manually
bash setup.sh
```

### Running Tests

```bash
# Run all tests
make test

# Run with coverage
make test-cov

# Run specific test file
pytest tests/test_core.py -v
```

### Building Documentation

```bash
# Build HTML docs
make docs

# Serve locally
cd docs && python -m http.server 8000
```

### Project Structure

```
planwise/
├── src/planwise/          # Main package
│   ├── core.py           # Core projection logic
│   ├── tax.py            # Tax calculations
│   ├── ni.py             # National Insurance
│   ├── plotting.py       # Visualization functions
│   ├── cli.py            # Command line interface
│   ├── profile.py        # User profile management
│   ├── databases.py      # Data loading utilities
│   └── data/             # Tax bands, limits, etc.
├── tests/                # Test suite
├── docs/                 # Documentation
├── streamlit_app.py      # Web application
├── pyproject.toml        # Project configuration
└── Makefile             # Development commands
```

## Contributing

Contributions are welcome! Please see our contributing guidelines:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes with tests
4. Run the test suite: `make test`
5. Check code quality: `make check-all`
6. Submit a pull request

### Code Style

- Follow PEP 8 style guidelines
- Use Black for code formatting
- Use isort for import sorting
- Add type hints for all public functions
- Write docstrings for all public APIs
- Maintain test coverage above 90%

### Adding New Features

When adding new features:

1. Add comprehensive tests in `tests/`
2. Update documentation in `docs/`
3. Add CLI options if applicable
4. Update the Streamlit app if relevant
5. Add examples to demonstrate usage

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This tool is for educational purposes only and does not provide financial advice. Tax rules and allowances may change, so consult a qualified financial adviser for personalised guidance.

**Key Assumptions:**
- Tax rules remain constant in nominal terms
- No carry-forward of unused allowances
- Pension contributions use the relief-at-source method
- Growth projections are simplified (no volatility)
- National Insurance rates are current as of 2025/26
- State pension projections use current rules

Always verify calculations with official HMRC guidance and consider seeking professional financial advice for important decisions.
