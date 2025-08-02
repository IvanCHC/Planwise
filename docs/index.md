# Planwise Documentation

Welcome to the Planwise documentation! This library helps you model retirement savings across various UK tax wrappers.

## Quick Start

```python
import planwise as pw

# Basic projection
results = pw.project_retirement(
    current_age=30,
    retirement_age=67,
    salary=40000,
    lisa_contrib_rate=0.05,
    isa_contrib_rate=0.05,
    sipp_employee_rate=0.05,
    sipp_employer_rate=0.0,
    workplace_employee_rate=0.05,
    workplace_employer_rate=0.03,
    shift_lisa_to_isa=0.5,
    shift_lisa_to_sipp=0.5,
    roi_lisa=0.05,
    roi_isa=0.05,
    roi_sipp=0.05,
    roi_workplace=0.05,
    inflation=0.02,
    scotland=False,
    use_qualifying_earnings=True,
)

print(results.head())
```

## API Reference

### Core Functions

#### `project_retirement()`

Main function for projecting retirement savings across multiple tax wrappers.

**Parameters:**
- `current_age` (int): Current age
- `retirement_age` (int): Target retirement age
- `salary` (float): Annual salary in pounds
- `lisa_contrib_rate` (float): LISA contribution rate (0-1)
- `isa_contrib_rate` (float): ISA contribution rate (0-1)
- `sipp_employee_rate` (float): SIPP employee contribution rate (0-1)
- `sipp_employer_rate` (float): SIPP employer contribution rate (0-1)
- `workplace_employee_rate` (float): Workplace pension employee rate (0-1)
- `workplace_employer_rate` (float): Workplace pension employer rate (0-1)
- `shift_lisa_to_isa` (float): Fraction of LISA redirected to ISA after age 50 (0-1)
- `shift_lisa_to_sipp` (float): Fraction of LISA redirected to SIPP after age 50 (0-1)
- `roi_lisa` (float): Expected LISA annual return (0-1)
- `roi_isa` (float): Expected ISA annual return (0-1)
- `roi_sipp` (float): Expected SIPP annual return (0-1)
- `roi_workplace` (float): Expected workplace pension annual return (0-1)
- `inflation` (float): Annual inflation rate (0-1)
- `scotland` (bool): Use Scottish tax bands if True
- `use_qualifying_earnings` (bool): Use qualifying earnings for workplace pension

**Returns:**
- `pd.DataFrame`: Year-by-year projection results

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
- `Tuple[List[TaxBand], float]`: List of TaxBand objects and personal allowance for the given year

### Plotting Functions

#### `make_contribution_plot(df, title=None)`

Create contribution breakdown chart.

#### `make_growth_plot(df, title=None)`

Create pot growth chart.

## Examples

See the `examples/` directory for more detailed usage examples.

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
- Assumes tax rules remain constant
- Ignores carry-forward of unused allowances
- Uses relief-at-source for pension contributions
- Doesn't consider National Insurance
- Uses simplified growth assumptions

Always consult a financial adviser for personalized advice.
