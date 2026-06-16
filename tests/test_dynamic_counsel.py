"""Spec for dynamic counsel invitation (series_a).

The negotiation room starts with only the two lead negotiators. Each lead
invites its own counsel mid-negotiation via ``band_add_participant``, then
consults by @mention. This is series_a behavior; patent_licensing keeps all
participants in the room from the start (invite_counsel defaults to False).
"""
from __future__ import annotations

import importlib

import pytest

from adapter_factory import _build_features
from scenarios.prompt_templates import build_lead_prompt

# (scenario, owner, the single other initial participant)
SCENARIO_TOPOLOGY = [
    ("series_a", "startup_ceo", "vc_partner"),
    ("patent_licensing", "tv_contract_attorney", "bg_licensing_counsel"),
]


def _lead(**overrides) -> str:
    kwargs = dict(
        identity="i", objectives="o", style="s", counsel_name="Startup Lawyer",
        opposing_lead="VC Partner", opposing_specialist="VC Lawyer",
        counsel_reference="r", concessions="c", topics="",
    )
    kwargs.update(overrides)
    return build_lead_prompt(**kwargs)


# ── Lead prompt: invite-counsel path ────────────────────────────────────────

def test_lead_prompt_invite_counsel_adds_participant_tool():
    p = _lead(invite_counsel=True)
    assert "band_add_participant" in p
    # Must be pinned to the lead's own counsel, by name.
    assert "Startup Lawyer" in p


def test_lead_prompt_default_does_not_invite():
    # Default (patent_licensing and any caller that doesn't opt in) is unchanged:
    # counsel is already in the room, so no add_participant instruction.
    p = _lead()
    assert "band_add_participant" not in p


def test_lead_prompt_never_loosens_other_room_controls():
    # Even when inviting counsel, the lead must not create rooms or look up peers.
    p = _lead(invite_counsel=True)
    assert "Never create chatrooms" in p or "never create chatrooms" in p.lower()
    assert "look up peers" in p.lower()


# ── Adapter features: only inviters get band_add_participant ─────────────────

def test_features_default_excludes_add_participant():
    f = _build_features(can_invite=False)
    assert "band_add_participant" in f.exclude_tools
    assert "band_lookup_peers" in f.exclude_tools
    assert "band_create_chatroom" in f.exclude_tools


def test_features_inviter_allows_add_participant_only():
    f = _build_features(can_invite=True)
    assert "band_add_participant" not in f.exclude_tools
    # The other room-management tools stay locked down.
    assert "band_lookup_peers" in f.exclude_tools
    assert "band_create_chatroom" in f.exclude_tools


# ── kickoff topology: both scenarios start with leads only ──────────────────

def _kickoff_room(scenario: str) -> dict:
    mod = importlib.import_module(f"scenarios.{scenario}.scenario")
    return mod.get_kickoff_config(agent_ids={}, agent_names={})["rooms"][0]


@pytest.mark.parametrize("scenario,owner,other_lead", SCENARIO_TOPOLOGY)
def test_room_starts_with_leads_only(scenario, owner, other_lead):
    room = _kickoff_room(scenario)
    assert room["owner"] == owner
    # The only other initial participant is the opposing lead — no specialists.
    assert room["participants"] == [other_lead]


@pytest.mark.parametrize("scenario,owner,other_lead", SCENARIO_TOPOLOGY)
def test_has_no_opening_briefings(scenario, owner, other_lead):
    # Counsel can't be briefed before they join, so the opening briefings are gone.
    room = _kickoff_room(scenario)
    assert not room.get("briefings")
