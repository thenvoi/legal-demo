"""Regression spec: team_subject_id injection reads the per-scenario config.

setup_agents.py writes credentials to ``agent_config.<scenario>.yaml`` (via
``credentials_path``), and ``load_credentials``/``kickoff.py`` read the same
file. ``inject_team_subject_id`` must read that exact file too — an earlier
version hardcoded ``agent_config.yaml`` (no scenario suffix), which is never
written, so every agent crashed with FileNotFoundError at startup.
"""
from __future__ import annotations

import yaml

import adapter_factory
from agent_config_ext import inject_team_subject_id


def test_injects_subject_id_from_per_scenario_config(tmp_path, monkeypatch):
    scenario = "series_a"
    cfg = tmp_path / f"agent_config.{scenario}.yaml"
    cfg.write_text(yaml.safe_dump({"startup_ceo": {"team_subject_id": "lead-123"}}))

    # credentials_path is the single source of truth for where the file lives.
    monkeypatch.setattr(adapter_factory, "ROOT_DIR", tmp_path)

    result = inject_team_subject_id("startup_ceo", "id=__TEAM_SUBJECT_ID__", scenario)
    assert result == "id=lead-123"


def test_missing_subject_id_replaces_with_empty(tmp_path, monkeypatch):
    scenario = "series_a"
    cfg = tmp_path / f"agent_config.{scenario}.yaml"
    cfg.write_text(yaml.safe_dump({"startup_ceo": {"agent_id": "a", "api_key": "k"}}))
    monkeypatch.setattr(adapter_factory, "ROOT_DIR", tmp_path)

    result = inject_team_subject_id("startup_ceo", "id=__TEAM_SUBJECT_ID__", scenario)
    assert result == "id="
