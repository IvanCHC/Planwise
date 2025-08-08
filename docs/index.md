# Planwise Documentation

Welcome to the Planwise documentation! This library helps you model retirement savings across various UK tax wrappers.

:::info
**Python Version Compatibility**

Planwise is tested on Python 3.11 and later.  Earlier Python versions (e.g., 3.8–3.10) are
not officially supported, although individual modules may still work.  Make sure your
environment is using Python 3.11+ before installing the package.
:::

## Quick Start

```python
import planwise as pw

from planwise.core import UserProfile, ContributionRates, InvestmentReturns

user = UserProfile(
    current_age=30,
    retirement_age=67,
    salary=40000,
    scotland=False,
)
contrib = ContributionRates(
    lisa=0.05,
    isa=0.05,
    sipp_employee=0.05,
    sipp_employer=0.0,
    workplace_employee=0.05,
    workplace_employer=0.03,
    shift_lisa_to_isa=0.5,
    shift_lisa_to_sipp=0.5,
)
returns = InvestmentReturns(
    lisa=0.05,
    isa=0.05,
    sipp=0.05,
    workplace=0.05,
)

results = pw.project_retirement(
    user=user,
    contrib=contrib,
    returns=returns,
    inflation=0.02,
    use_qualifying_earnings=True,
    year=2025,
)

print(results.head())
```

## API Reference

### Core Functions

#### `project_retirement(user, contrib, returns, inflation, use_qualifying_earnings, year)`

Main function for projecting retirement savings across multiple tax wrappers.

**Parameters:**
- `user` ([`planwise.core.UserProfile`](src/planwise/core.py)): User profile including age, retirement age, salary, and region.
- `contrib` ([`planwise.core.ContributionRates`](src/planwise/core.py)): Contribution rates for each wrapper and shift rates after age 50.
- `returns` ([`planwise.core.InvestmentReturns`](src/planwise/core.py)): Expected annual rates of return for each wrapper.
- `inflation` (float): Annual inflation rate (0-1)
- `use_qualifying_earnings` (bool): Use qualifying earnings for workplace pension
- `year` (int): Tax year (e.g., 2025 for 2025/26)

**Returns:**
- `pd.DataFrame`: Year-by-year projection results

#### `RetirementSimulator`

While the :func:`project_retirement` convenience function remains available for
backwards compatibility, the underlying projection logic is encapsulated in
the :class:`planwise.core.RetirementSimulator` class.  This class stores
the input parameters and internal state and exposes a :meth:`simulate`
method that returns a ``DataFrame`` identical to the result from
``project_retirement``.  Using the class directly makes it easier to
understand and modify intermediate steps, since the year–by–year logic is
organized into small helper methods rather than a single monolithic
function.

Example:

```python
from planwise.core import UserProfile, ContributionRates, InvestmentReturns, IncomeBreakdown, RetirementSimulator

# Define inputs as usual
user = UserProfile(current_age=30, retirement_age=67, salary=40000, scotland=False)
contrib = ContributionRates(lisa=0.05, isa=0.05, sipp_employee=0.05, sipp_employer=0.0,
                            workplace_employee=0.05, workplace_employer=0.03,
                            shift_lisa_to_isa=0.5, shift_lisa_to_sipp=0.5)
returns = InvestmentReturns(lisa=0.05, isa=0.05, sipp=0.05, workplace=0.05)
income = IncomeBreakdown(salary=user.salary, take_home_salary=user.salary, income_tax=0.0, ni_due=0.0)

# Instantiate the simulator and run the projection
simulator = RetirementSimulator(
    user=user,
    contrib=contrib,
    returns=returns,
    income=income,
    inflation=0.02,
    use_qualifying_earnings=True,
    year=2025,
)
results = simulator.simulate()
print(results.head())
```

Internally, the simulator breaks the calculations into helper methods that
compute the base for workplace contributions, apply the pension annual
allowance, calculate tax relief and update pots.  This design makes it
easier to extend or override specific behaviours without rewriting the
entire projection loop.

#### `UserProfile`

Dataclass for user profile:
- `current_age` (int)
- `retirement_age` (int)
- `salary` (float)
- `scotland` (bool)

#### `ContributionRates`

Dataclass for contribution rates:
- `lisa` (float)
- `isa` (float)
- `sipp_employee` (float)
- `sipp_employer` (float)
- `workplace_employee` (float)
- `workplace_employer` (float)
- `shift_lisa_to_isa` (float)
- `shift_lisa_to_sipp` (float)

#### `InvestmentReturns`

Dataclass for investment returns:
- `lisa` (float)
- `isa` (float)
- `sipp` (float)
- `workplace` (float)

#### `IncomeBreakdown`

Dataclass for income breakdown:
- `salary` (float)
- `take_home_salary` (float)
- `income_tax` (float)
- `ni_due` (float)

### Tax Functions

#### `calculate_income_tax(income, scotland, year)`

Calculate income tax for a given income, region, and tax year.

**Parameters:**
- `income` (float): Taxable income (after personal allowance and before relief adjustments)
- `scotland` (bool): Use Scottish tax bands if True
- `year` (int): Tax year (e.g., 2025 for 2025/26)

**Returns:**
- `float`: Tax payable in pounds

#### `get_tax_bands(scotland, year)`

Get tax bands and personal allowance for a region and tax year.

**Parameters:**
- `scotland` (bool): Use Scottish tax bands if True
- `year` (int): Tax year (e.g., 2025 for 2025/26)

**Returns:**
- `Tuple[List[TaxBand], float]`: List of [`planwise.tax.TaxBand`](src/planwise/tax.py) objects and personal allowance for the given year

### National Insurance Functions

#### `calculate_ni(income, year=2025, category="category_a")`

Calculate National Insurance contributions for a given income, year, and category.

**Parameters:**
- `income` (float): Gross annual income
- `year` (int): Tax year (default 2025)
- `category` (str): NI category (default "category_a")

**Returns:**
- `float`: National Insurance contribution due

#### `get_ni_bands(year=2025, category="category_a")`

Get NI bands for a given year and category.

**Parameters:**
- `year` (int): Tax year
- `category` (str): NI category

**Returns:**
- `List[NICBand]`: List of [`planwise.ni.NICBand`](src/planwise/ni.py) objects

## Command Line Interface

Planwise provides a command‑line interface (CLI) via the `planwise`
console script.  It allows you to run retirement projections without
writing any code.  Contribution rates are expressed as fractions of your
*take‑home salary* (gross salary minus income tax and National Insurance).
The CLI automatically calculates your net pay based on the selected tax
year and whether you are a Scottish taxpayer, ensuring that contribution
limits and pension annual allowance rules are applied consistently.

### Usage

The simplest usage is:

```bash
planwise --current-age 30 --retirement-age 67 --salary 40000
```

This runs a projection using default contribution rates and prints a
detailed year‑by‑year table to the terminal.

### Options

| Option | Description |
|-------|-------------|
| `--current-age` | Current age of the individual (default: 30) |
| `--retirement-age` | Age at which saving stops and projection ends (default: 67) |
| `--salary` | Gross annual salary in pounds (required) |
| `--lisa-rate` | Fraction of take‑home pay contributed to a Lifetime ISA (default: 0.05) |
| `--isa-rate` | Fraction of take‑home pay contributed to a Stocks & Shares ISA (default: 0.05) |
| `--sipp-employee-rate` | Employee contribution to a SIPP as a fraction of take‑home pay (default: 0.05) |
| `--sipp-employer-rate` | Employer contribution to a SIPP as a fraction of take‑home pay (default: 0.0) |
| `--workplace-employee-rate` | Employee contribution to the workplace pension (default: 0.05) |
| `--workplace-employer-rate` | Employer contribution to the workplace pension (default: 0.03) |
| `--shift-lisa-to-isa` | After age 50, fraction of the former LISA contribution redirected to the ISA (default: 0.5) |
| `--shift-lisa-to-sipp` | After age 50, fraction of the former LISA contribution redirected to the SIPP (default: 0.5) |
| `--roi-<wrapper>` | Expected annual return for each wrapper (`lisa`, `isa`, `sipp`, `workplace`; default 0.05) |
| `--inflation` | Annual inflation assumption (default: 0.02) |
| `--scotland` | Use Scottish income tax bands instead of rest‑of‑UK |
| `--use-qualifying-earnings` | Calculate workplace contributions on qualifying earnings instead of full salary |
| `--tax-year` | Tax year used for allowances and tax bands (default: latest available) |
| `--summary` | Display a concise summary of the final pot values instead of the full table |
| `--output` | Path to write the full results as a CSV file |
| `--config` | Load CLI arguments from a JSON configuration file |

### Examples

```bash
# Run a projection and view a detailed table
planwise --current-age 30 --retirement-age 67 --salary 40000

# Summarise final pot values
planwise --current-age 30 --retirement-age 67 --salary 40000 --summary

# Use Scottish tax bands and save results to CSV
planwise --current-age 30 --retirement-age 67 --salary 40000 --scotland --output results.csv

# Load parameters from a JSON file
planwise --config params.json --summary
```

Plotting functions (such as ``RetirementPlotter`` and ``make_growth_plot``) are
not available unless the optional plotting dependencies are installed.  To
enable plotting support, install the ``planwise[plotting]`` extras.  If you
attempt to call a plotting function without the necessary dependencies you
will receive an informative error message.

### Plotting API

Visualization of projection data is provided by the :class:`planwise.plotting.RetirementPlotter` class.  The class accepts a DataFrame from :func:`planwise.core.project_retirement` and exposes methods to build Altair charts for contributions, pot growth and a combined view:

* ``RetirementPlotter.contribution_chart(title=None)`` – return a stacked bar chart showing the share of net contributions by account.  Pass a custom ``title`` to override the default.
* ``RetirementPlotter.growth_chart(title=None)`` – return a line chart showing both pot values and accumulated contributions for each account.  Pots are drawn with solid lines while accumulated contributions are drawn with dashed lines.  If the DataFrame lacks pre‑computed accumulated columns, cumulative sums of the annual net contributions are computed on the fly.
* ``RetirementPlotter.combined_chart(contrib_title=None, growth_title=None)`` – horizontally concatenate the contributions and growth charts into a single figure.

For convenience and backward compatibility, the module still exports the functions ``make_contribution_plot(df, title=None)``, ``make_growth_plot(df, title=None)`` and ``make_combined_plot(df)`` which simply instantiate a :class:`RetirementPlotter` internally and delegate to the corresponding methods.


## UK Tax Rules

The library implements 2025/26 tax year rules:

### Income Tax Bands

**Rest of UK:**
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

- ISA allowance: £20,000/year
- LISA allowance: £4,000/year (until age 50)
- Pension annual allowance: £60,000/year
- Qualifying earnings: £6,240 - £50,270

## Limitations

This is a simplified model that:
* Assumes tax rules remain constant
* Ignores carry‑forward of unused allowances
* Uses relief‑at‑source for pension contributions
* Includes National Insurance and income tax only to calculate take‑home salary;
  it does **not** simulate NI or tax payments beyond the contribution stage
* Uses simplified growth assumptions

Always consult a financial adviser for personalized advice.
