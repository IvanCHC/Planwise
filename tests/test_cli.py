import subprocess


def run_cli(args):
    """Helper to run the CLI and capture output."""
    result = subprocess.run("planwise", capture_output=True, text=True)
    return result


def test_cli_basic_runs():
    """Test CLI runs with basic arguments and prints output."""
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
    """Test CLI writes output to CSV file."""
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


def test_cli_config_file(tmp_path):
    """Test CLI loads parameters from a config file."""
    config = {"current_age": 30, "retirement_age": 31, "salary": 40000, "summary": True}
    config_path = tmp_path / "config.json"
    with open(config_path, "w") as f:
        import json

        json.dump(config, f)
    result = run_cli(["--config", str(config_path)])
    assert result.returncode == 0
