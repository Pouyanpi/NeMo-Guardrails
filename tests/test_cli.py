from typer.testing import CliRunner

from colangflows.cli import app

runner = CliRunner()


def test_app():
    result = runner.invoke(
        app,
        [
            "chat",
            "--config=examples/rails/benefits_co/config.yml",
            "--config=examples/rails/benefits_co/general.co",
        ],
    )
    assert result.exit_code == 1
    assert "not supported" in result.stdout
    assert "Please provide a single" in result.stdout
