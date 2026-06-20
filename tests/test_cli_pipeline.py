"""End-to-end smoke: the CLI subcommands run and exit 0."""

from __future__ import annotations

from stackfund.cli import main


def test_pipeline_runs():
    assert main(["pipeline"]) == 0


def test_verify_is_deterministic():
    assert main(["verify"]) == 0


def test_crowd_runs():
    assert main(["crowd", "--symbol", "0056"]) == 0
