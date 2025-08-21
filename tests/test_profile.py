from pathlib import Path

from planwise import profile

qualifying_earnings = profile.QualifyingEarnings(
    use_qualifying_earnings=True,
    qualifying_earnings=10000,
    qualifying_upper=50000,
    qualifying_lower=40000,
)
personal_details = profile.PersonalDetails(
    current_age=30,
    retirement_age=65,
    salary=50000,
    take_home_salary=35000,
    ni_contribution=3000,
    income_tax=12000,
)
contribution_settings = profile.ContributionSettings(
    workplace_er_rate=0.03,
    workplace_er_contribution=1500,
    workplace_ee_rate=0.05,
    workplace_ee_contribution=2500,
    lisa_rate=0.1,
    lisa_contribution=3500,
    isa_rate=0.2,
    isa_contribution=7000,
    sipp_rate=0.05,
    sipp_contribution=1750,
    total_workplace_contribution=4000,
    total_sipp_contribution=1750,
    total_isa_contribution=7000,
    total_net_contribution=12750,
    total_pension_contribution=5750,
)
account_balances = profile.AccountBalances(
    lisa_balance=10000,
    isa_balance=20000,
    sipp_balance=30000,
    workplace_pension_balance=40000,
)
post_50_contribution_settings = profile.Post50ContributionSettings(
    post_50_lisa_to_isa_rate=0.6,
    post_50_lisa_to_isa_contribution=2100,
    post_50_lisa_to_sipp_rate=0.4,
    post_50_lisa_to_sipp_contribution=1400,
)
expected_returns_and_inflation = profile.ExpectedReturnsAndInflation(
    expected_lisa_annual_return=0.05,
    expected_isa_annual_return=0.06,
    expected_sipp_annual_return=0.07,
    expected_workplace_annual_return=0.04,
    expected_inflation=0.02,
)
post_retirement_settings = profile.PostRetirementSettings(
    withdrawal_today_amount=20000,
    expected_post_retirement_lisa_annual_return=0.03,
    expected_post_retirement_isa_annual_return=0.04,
    expected_post_retirement_pension_annual_return=0.05,
    postret_lisa_withdrawal_age=60,
    postret_lisa_targeted_withdrawal_percentage=0.1,
    postret_isa_withdrawal_age=61,
    postret_isa_targeted_withdrawal_percentage=0.2,
    postret_taxfree_pension_withdrawal_age=62,
    postret_taxfree_pension_targeted_withdrawal_percentage=0.3,
    postret_taxable_pension_withdrawal_age=63,
    postret_taxable_pension_targeted_withdrawal_percentage=0.4,
)

profile_settings = profile.ProfileSettings(
    tax_year=2023,
    scotland=False,
    qualifying_earnings=qualifying_earnings,
    personal_details=personal_details,
    contribution_settings=contribution_settings,
    account_balances=account_balances,
    post_50_contribution_settings=post_50_contribution_settings,
    expected_returns_and_inflation=expected_returns_and_inflation,
    post_retirement_settings=post_retirement_settings,
)


def test_safe_filename():
    assert profile.safe_filename("Test Profile!@#") == "Test Profile___"
    assert profile.safe_filename("A" * 100) == "A" * 80


def test_profile_path():
    name = "TestProfile"
    path = profile.profile_path(name)
    assert isinstance(path, Path)
    assert path.name.startswith("TestProfile")


def test_serialise_and_deserialise_profile_settings(tmp_path):
    file_path = tmp_path / "test_profile.json"
    profile.serialise_profile_settings_to_json(profile_settings, file_path)
    loaded = profile.deserialise_profile_settings_from_json(file_path)
    assert isinstance(loaded, profile.ProfileSettings)
    assert loaded.tax_year == profile_settings.tax_year
    assert loaded.personal_details.salary == profile_settings.personal_details.salary


def test_save_and_load_profile(tmp_path, monkeypatch):
    monkeypatch.setattr(profile, "PROFILES_DIR", tmp_path)
    name = "UnitTestProfile"
    profile.save_profile(name, profile_settings)
    loaded = profile.load_profile(name)
    assert isinstance(loaded, profile.ProfileSettings)
    assert loaded.account_balances.lisa_balance == 10000
    profile.delete_profile(name)
    assert profile.load_profile(name) is None


def test_list_profiles(tmp_path, monkeypatch):
    monkeypatch.setattr(profile, "PROFILES_DIR", tmp_path)
    name1 = "Profile1"
    name2 = "Profile2"
    profile.save_profile(name1, profile_settings)
    profile.save_profile(name2, profile_settings)
    profiles = profile.list_profiles()
    assert name1 in profiles and name2 in profiles


def test_get_qualifying_earnings_info():
    result = profile.get_qualifying_earnings_info(True, 2025)
    assert isinstance(result, profile.QualifyingEarnings)
    assert result.use_qualifying_earnings is True


def test_get_personal_details():
    details = profile.get_personal_details(30, 65, 50000, 2025, False)
    assert isinstance(details, profile.PersonalDetails)
    assert details.current_age == 30
    assert details.salary == 50000


def test_get_workplace_contribution_rate():
    rate, amount = profile.get_workplace_contribution_rate(
        0.05, personal_details, qualifying_earnings
    )
    assert isinstance(rate, float)
    assert isinstance(amount, float)
    rate2, amount2 = profile.get_workplace_contribution_rate(
        2500, personal_details, qualifying_earnings, use_exact_amount=True
    )
    assert isinstance(rate2, float)
    assert amount2 == 2500


def test_get_isa_contribution_rate():
    rate, amount = profile.get_isa_contribution_rate(0.2, personal_details)
    assert isinstance(rate, float)
    assert isinstance(amount, float)
    rate2, amount2 = profile.get_isa_contribution_rate(
        7000, personal_details, use_exact_amount=True
    )
    assert isinstance(rate2, float)
    assert amount2 == 7000


def test_get_sipp_contribution_rate():
    rate, amount = profile.get_sipp_contribution_rate(0.05, personal_details)
    assert isinstance(rate, float)
    assert isinstance(amount, float)
    rate2, amount2 = profile.get_sipp_contribution_rate(
        1750, personal_details, use_exact_amount=True
    )
    assert isinstance(rate2, float)
    assert amount2 == 1750


def test_get_post_50_contribution_settings():
    result = profile.get_post_50_contribution_settings(False, 0.6, 3500)
    assert isinstance(result, profile.Post50ContributionSettings)
    assert result.post_50_lisa_to_isa_rate == 0.6
    result2 = profile.get_post_50_contribution_settings(True, 2100, 3500)
    assert isinstance(result2, profile.Post50ContributionSettings)
    assert result2.post_50_lisa_to_isa_contribution == 2100
