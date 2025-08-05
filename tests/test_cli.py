"""
Tests for the Planwise CLI interface.

These tests check that the CLI runs with various argument combinations, writes output to CSV,
and loads configuration from a JSON file.
"""

import subprocess


def run_cli(args):
    """
    Helper to run the CLI and capture output.
    Args:
        args (list): List of CLI arguments.
    Returns:
        CompletedProcess: Result of subprocess.run.
    """
    # Note: Replace 'planwise' with the actual CLI entry point if needed.
    result = subprocess.run(["planwise"] + args, capture_output=True, text=True)
    return result


def test_cli_basic_runs():
    """
    Test CLI runs with basic arguments and prints output.
    Checks that the CLI exits successfully.
    """
    result = run_cli(
        [
            "--current-age",
            "30",
            "--retirement-age",
            "32",
            "--salary",
            "40000",
            "--summary",
        ]
    )
    assert result.returncode == 0


def test_cli_output_csv(tmp_path):
    """
    Test CLI writes output to a CSV file.
    Checks that the CLI exits successfully and the file is created.
    """
    out_file = tmp_path / "out.csv"
    result = run_cli(
        [
            "--current-age",
            "30",
            "--retirement-age",
            "32",
            "--salary",
            "40000",
            "--output",
            str(out_file),
        ]
    )
    assert result.returncode == 0
    assert out_file.exists()


def test_cli_config_file(tmp_path):
    """
    Test CLI loads parameters from a config file.
    Checks that the CLI exits successfully when using a JSON config.
    """
    config = {"current_age": 30, "retirement_age": 31, "salary": 40000, "summary": True}
    config_path = tmp_path / "config.json"
    with open(config_path, "w") as f:
        import json

        json.dump(config, f)
    result = run_cli(["--config", str(config_path)])
    assert result.returncode == 0
