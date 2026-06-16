# Legal Demo: Multi-Agent Negotiation

A multi-agent negotiation demo where 4 AI agents, built on different frameworks,
negotiate through the [Band](https://app.thenvoi.com) platform. Each scenario gives the
agents their own personas, domain prompts, and starting positions; they argue, pull in
their counsel, and work toward an agreement in a shared room.

Prepared for the Stanford LLM × Law hackathon (2026).

## Scenarios

Two scenarios ship with the demo. `series_a` is the default.

| Scenario | Parties | What they negotiate |
|---|---|---|
| `series_a` (default) | NovaTech (startup) vs. Apex Ventures (VC) | Series A valuation, investment amount, board composition |
| `patent_licensing` | TechVentures (buyer) vs. BioGen Therapeutics (seller) | Patent-licensing royalty rate and license scope |

Each scenario has 4 agents: two lead negotiators (one per side) and two counsel/specialists.
The leads drive the conversation; counsel only speak when their principal @mentions them.
Everyone shares one room, so the opposing side sees everything — counsel use guarded
language accordingly.

### `series_a` agents (default)

| Agent | Org | Framework | Role |
|---|---|---|---|
| Startup CEO | NovaTech | LangGraph | Lead negotiator — maximize valuation, keep founder control |
| Startup Lawyer | NovaTech | PydanticAI | Counsel on term-sheet provisions and governance |
| VC Partner | Apex Ventures | LangGraph | Lead negotiator — target equity stake, investor protections |
| VC Lawyer | Apex Ventures | PydanticAI | Counsel on deal structure and downside protection |

### `patent_licensing` agents

| Agent | Org | Framework | Role |
|---|---|---|---|
| Contract Attorney | TechVentures | LangGraph | Lead buyer negotiator — broad license, low royalties |
| IP Analyst | TechVentures | PydanticAI | Patent-scope analysis, prior-art leverage |
| Licensing Counsel | BioGen | PydanticAI | Lead seller negotiator — protect IP, maximize revenue |
| Regulatory Advisor | BioGen | PydanticAI | FDA / EAR / GDPR compliance |

Framework and model are configured per agent in `scenarios/<scenario>/agents.yaml`.
`series_a` agents run on Claude (Anthropic); `patent_licensing` agents run on GPT.
The adapter factory (`adapter_factory.py`) also supports the Anthropic SDK, CrewAI,
Letta, and Parlant adapters if you want to swap a framework.

## What This Demonstrates

| Band capability | How it shows up |
|---|---|
| **Cross-framework interop** | LangGraph and PydanticAI agents collaborate in one room |
| **Cross-organizational comms** | Agents from opposing companies negotiate through a shared room |
| **@mention routing** | Agents address each other by name; the platform routes and gates messages |
| **Mention-filtered visibility** | Agents only see messages they're @mentioned in; counsel stay quiet until pulled in |
| **Specialist escalation** | Leads add their own counsel mid-negotiation via `band_add_participant` |
| **Thought events** | Agents share internal strategy notes via `band_send_event` |
| **Long-term memory (optional)** | Team strategy seeded as org-scoped memories, gated behind `BAND_ENABLE_MEMORY` |

**NovaTech** (AI-powered drug discovery, $1.2M ARR) is raising a $5M Series A from **Apex Ventures**. Both sides have walk-away lines. Counsel only speaks when @mentioned by their principal.

### 1. Configure environment

```bash
cp .env.example .env
# Edit .env with your API keys
```

You need:
- `BAND_API_KEY_USER` — a User API key from your Band account settings. Used by
  `setup_agents.py` to register agents and by `kickoff.py` for room setup.
- `ANTHROPIC_API_KEY` — for the `series_a` agents (Claude).
- `OPENAI_API_KEY` — for the `patent_licensing` agents (GPT).

Optional:
- `BAND_API_KEY_USER_STARTUP` / `BAND_API_KEY_USER_VC` — per-team User API keys. When
  set, each team's agents register under its own account so team-strategy memories stay
  isolated. Both fall back to `BAND_API_KEY_USER` when unset.
- `BAND_ENABLE_MEMORY=1` — enable the platform Memory API (Enterprise plan only).
  When unset, the demo runs without memory: no team-strategy seeding, no memory tools.

### 2. Install dependencies

```bash
cp agent_config.series_a.yaml.example agent_config.series_a.yaml
# Paste agent_id and api_key for each agent
```

### 3. Register agents on the platform

```bash
python setup_agents.py                                # series_a (default)
python setup_agents.py --scenario patent_licensing    # patent_licensing
```

This deletes the scenario's existing agents, re-registers them, and writes their
credentials to `agent_config.yaml`. Tear them down with `python setup_agents.py --delete`.

### 4. Start the agents

```bash
python run_all.py                                     # series_a (default)
python run_all.py --scenario patent_licensing         # patent_licensing
python run_all.py --scenario series_a vc_*            # launch a subset (glob patterns)
```

Press Ctrl+C to shut all of them down.

### 5. Kick off the negotiation

In a separate terminal, once the agents are running:

```bash
python kickoff.py                                     # series_a (default)
python kickoff.py --scenario patent_licensing         # patent_licensing
python kickoff.py --no-clean                          # skip deactivating old rooms
python kickoff.py --message "Custom kickoff..."       # custom kickoff message
```

`kickoff.py` creates a single negotiation room, adds the two lead negotiators, and sends
the opening message from the side that starts. By default it first cleans up old rooms
(removes participants — the API has no delete-room endpoint); use `--no-clean` to skip.

Watch the negotiation unfold in the Band platform UI.

---

- Each agent is a standalone Python process connected to Band over a WebSocket.
  `run_all.py` spawns one `multiprocessing.Process` per agent.
- Agent behavior is driven entirely by system-prompt strings (`CUSTOM_SECTION` in each
  agent module, assembled from `scenarios/prompt_templates.py`) — not hardcoded logic.
- Adapters are built by `adapter_factory.py` from each scenario's `agents.yaml`, so you
  can change an agent's framework or model without touching the negotiation logic.
- Room/peer-management tools (`band_lookup_peers`, `band_create_chatroom`) are excluded
  from every agent; lead negotiators keep `band_add_participant` so they can pull in
  their counsel by name.
- The platform handles message routing, room management, mention-gated visibility, and
  presence — agents just process messages and call tools.

See [`CLAUDE.md`](CLAUDE.md) for the full scenario layout and the Band platform reference.
