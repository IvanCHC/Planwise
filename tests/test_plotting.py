import altair as alt
import pandas as pd

from planwise import plotting


def test_plot_pie_chart_breakdown_normal():
    breakdown = {"ISA": 1000, "SIPP": 2000, "LISA": 500}
    chart = plotting.plot_pie_chart_breakdown(breakdown)
    assert isinstance(chart, alt.LayerChart)


def test_plot_pie_chart_breakdown_empty():
    chart = plotting.plot_pie_chart_breakdown({})
    assert isinstance(chart, alt.Chart)


def test_plot_annual_contribution_chart_normal():
    df = pd.DataFrame(
        {
            "Age": [30, 31],
            "LISA Net": [100, 150],
            "ISA Net": [200, 250],
            "SIPP Net": [300, 350],
            "Workplace EE Net": [400, 450],
        }
    )
    chart = plotting.plot_annual_contribution_chart(df)
    assert isinstance(chart, alt.Chart)


def test_plot_annual_contribution_chart_empty():
    df = pd.DataFrame(
        {
            "Age": [],
            "LISA Net": [],
            "ISA Net": [],
            "SIPP Net": [],
            "Workplace EE Net": [],
        }
    )
    chart = plotting.plot_annual_contribution_chart(df)
    assert isinstance(chart, alt.Chart)


def test_plot_growth_projection_chart_normal():
    df = pd.DataFrame(
        {
            "Age": [30, 31],
            "Portfolio Balance": [1000, 1100],
            "LISA Balance": [200, 220],
            "ISA Balance": [300, 330],
            "SIPP Balance": [400, 440],
            "Workplace Balance": [500, 550],
        }
    )
    chart = plotting.plot_growth_projection_chart(df)
    assert isinstance(chart, alt.Chart)


def test_plot_growth_projection_chart_empty():
    df = pd.DataFrame(
        {
            "Age": [],
            "Portfolio Balance": [],
            "LISA Balance": [],
            "ISA Balance": [],
            "SIPP Balance": [],
            "Workplace Balance": [],
        }
    )
    chart = plotting.plot_growth_projection_chart(df)
    assert isinstance(chart, alt.Chart)


def test_plot_withdrawals_by_account_chart_normal():
    df = pd.DataFrame(
        {
            "Age": [65, 66],
            "Withdrawal LISA Today": [100, 110],
            "Withdrawal ISA Today": [200, 210],
            "Withdrawal Tax-Free Pension Today": [300, 310],
            "Withdrawal Taxable Pension Today": [400, 410],
            "Withdrawal State Pension Today": [500, 510],
            "Withdrawal Shortfall Today": [0, 0],
        }
    )
    chart = plotting.plot_withdrawals_by_account_chart(df)
    assert isinstance(chart, alt.Chart)


def test_plot_withdrawals_by_account_chart_empty():
    df = pd.DataFrame(
        {
            "Age": [],
            "Withdrawal LISA Today": [],
            "Withdrawal ISA Today": [],
            "Withdrawal Tax-Free Pension Today": [],
            "Withdrawal Taxable Pension Today": [],
            "Withdrawal State Pension Today": [],
            "Withdrawal Shortfall Today": [],
        }
    )
    chart = plotting.plot_withdrawals_by_account_chart(df)
    assert isinstance(chart, alt.Chart)


def test_plot_total_withdrawals_chart_normal():
    df = pd.DataFrame(
        {
            "Age": [65, 66],
            "Total Withdrawal Today": [1000, 1100],
            "Total Withdrawal After Tax Today": [900, 1000],
            "Income Tax Today": [100, 100],
        }
    )
    chart = plotting.plot_total_withdrawals_chart(df)
    assert isinstance(chart, alt.Chart)


def test_plot_total_withdrawals_chart_empty():
    df = pd.DataFrame(
        {
            "Age": [],
            "Total Withdrawal Today": [],
            "Total Withdrawal After Tax Today": [],
            "Income Tax Today": [],
        }
    )
    chart = plotting.plot_total_withdrawals_chart(df)
    assert isinstance(chart, alt.Chart)


def test_plot_balances_by_account_chart_normal():
    df = pd.DataFrame(
        {
            "Age": [65, 66],
            "LISA Balance Today": [100, 110],
            "ISA Balance Today": [200, 210],
            "Tax-Free Pension Balance Today": [300, 310],
            "Taxable Pension Balance Today": [400, 410],
        }
    )
    chart = plotting.plot_balances_by_account_chart(df)
    assert isinstance(chart, alt.Chart)


def test_plot_balances_by_account_chart_empty():
    df = pd.DataFrame(
        {
            "Age": [],
            "LISA Balance Today": [],
            "ISA Balance Today": [],
            "Tax-Free Pension Balance Today": [],
            "Taxable Pension Balance Today": [],
        }
    )
    chart = plotting.plot_balances_by_account_chart(df)
    assert isinstance(chart, alt.Chart)


def test_plot_total_balance_chart_normal():
    df = pd.DataFrame({"Age": [65, 66], "Total Balance Today": [1000, 1100]})
    chart = plotting.plot_total_balance_chart(df)
    assert isinstance(chart, alt.Chart)


def test_plot_total_balance_chart_empty():
    df = pd.DataFrame({"Age": [], "Total Balance Today": []})
    chart = plotting.plot_total_balance_chart(df)
    assert isinstance(chart, alt.Chart)
