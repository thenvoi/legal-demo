# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

A multi-agent negotiation demo where 4 AI agents negotiate through the Thenvoi platform. Supports multiple negotiation scenarios, each with its own agents, domain-specific prompts, and isolated credentials. All four agents in a scenario share a single room.

Every agent is framework-agnostic: the choice of adapter (`codex`, `claude_sdk`, `anthropic`, `pydantic_ai`, `langgraph`, `gemini`, `google_adk`) is driven by a per-scenario `agents.yaml`, not hardcoded in the agent module. Swap any agent to a different framework by editing yaml alone. Current defaults: `series_a` ships 1 `pydantic_ai` + 3 `langgraph` on `gpt-5.4`; `patent_licensing` ships 1 `langgraph` + 3 `pydantic_ai` on `gpt-5.4-mini`. Both default mixes require `OPENAI_API_KEY`. Each `agents.yaml` has commented alternative blocks at the top (codex subscription, claude_sdk subscription, langgraph + local model) so switching away from OpenAI is a copy-paste, not a refactor.

**Available scenarios:**
- `series_a` (default) — NovaTech (startup) + Apex Ventures (VC) negotiate Series A funding terms
- `patent_licensing` — TechVentures (buyer) + BioGen (seller) negotiate a patent-licensing agreement

## Commands

```bash
# Setup
cp .env.example .env                                     # fill in THENVOI_API_KEY_USER
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# setup_agents.py deletes this scenario's existing agents, then re-registers them.
python setup_agents.py                         # registers agents for series_a (default)
python setup_agents.py --scenario patent_licensing  # registers patent_licensing agents
python setup_agents.py --delete                # tears down the scenario's agents

# Run
python run_all.py                              # launches series_a agents (default)
python run_all.py --scenario patent_licensing  # launches patent_licensing agents
python run_all.py --scenario series_a vc_*     # launch subset (glob patterns)

# Kickoff (separate terminal, after agents are running)
python kickoff.py                              # starts series_a negotiation (default)
python kickoff.py --scenario patent_licensing  # starts patent_licensing negotiation
python kickoff.py --no-clean                   # skip deactivating old rooms
python kickoff.py --message "..."              # custom kickoff message
```

No test suite or linting config exists yet.

## Architecture

**Scenario structure:**
```
scenarios/
  series_a/
    scenario.py          # AGENTS, AGENT_MODULES, get_kickoff_config()
    agents.yaml          # per-agent framework + model + adapter options
    startup_ceo.py
    startup_lawyer.py
    vc_partner.py
    vc_lawyer.py
```

Each `scenario.py` exports:
- `AGENTS` — list of agent definitions for `setup_agents.py` (config_key, name, description)
- `AGENT_MODULES` — module paths for `run_all.py`
- `get_kickoff_config(agent_ids, agent_names)` — room topology + messages for `kickoff.py`

Each `agents.yaml` maps `config_key` → adapter config. `framework` and `model` are required; every other key (e.g. `reasoning_effort`, `max_thinking_tokens`, `temperature`) is forwarded into the adapter constructor by `adapter_factory.create_adapter`. That means adding an adapter-specific knob never requires factory edits.

**Config key invariant:** for each agent, the module filename, the `config_key` in `scenario.py`'s `AGENTS`, the key in `agents.yaml`, and the argument to `create_adapter`/`load_credentials` must all match. See `vc_legal_counsel` across the series_a scenario for the canonical pattern.

**Core pattern** (all agents follow this):
```python
scenario = os.path.basename(os.path.dirname(__file__))
agent_id, api_key = load_credentials("<key>", scenario)
adapter = create_adapter("<key>", CUSTOM_SECTION, scenario)
agent = Agent.create(adapter=adapter, agent_id=agent_id, api_key=api_key, ...)
await agent.run()
```

Agent behavior is driven by detailed `CUSTOM_SECTION` system prompt strings, not hardcoded logic.

**Communication topology (1 room per scenario, created by `kickoff.py`):**
- **Single negotiation room**: 2 lead negotiators + 2 counsel/specialists
- Lead negotiators drive the conversation; counsel/specialists only respond when @mentioned by their principal
- Counsel/specialists use guarded language since the opposing side can see everything

**Data flow:**
- `setup_agents.py` uses REST (`thenvoi_rest.AsyncRestClient` with the User API key) to register agents and get per-agent credentials, written to `agent_config.<scenario>.yaml`
- `kickoff.py` reads `agent_config.<scenario>.yaml`, creates rooms, adds participants, and sends kickoff/briefing messages based on `scenario.py`
- `run_all.py` spawns each agent as a `multiprocessing.Process`; each calls `asyncio.run(agent_module.main())`
- At runtime, agents connect via WebSocket and use Band tools: `band_send_event`, `band_send_message`, etc.

**Tool filtering:** `tool_filter.remove_tools(...)` pops entries from `thenvoi.runtime.tools.TOOL_DEFINITIONS`. Every adapter that reads tools through `AgentToolsProtocol.get_tool_schemas` (codex, anthropic, pydantic_ai, claude_sdk, gemini, google_adk) is filtered by that single pop. LangGraph and CrewAI have their own tool builders and are monkey-patched separately — each patch is guarded by `try/except ImportError`, so the filter works fine on environments without those optional deps.

**MCP integration:** `mcp_tools.MCPToolsProvider` wraps the official `mcp` Python client and turns any stdio or streamable-HTTP MCP server's tool list into portable `CustomToolDef` tuples that slot into `create_adapter(..., additional_tools=...)`. The provider uses an `AsyncExitStack` for lifetime management; typical use is `await provider.start()` near the top of an agent module's `main()` and `await provider.stop()` in a `finally` block, or the `async with` form. Only the five portable-format adapters (codex, claude_sdk, anthropic, gemini, google_adk) can consume the output — pydantic_ai and langgraph want framework-native formats, so swap those agents' frameworks first if you need MCP on them.

**Key config files:**
<<<<<<< HEAD
- `.env` (see `.env.example`):
  - `BAND_API_KEY_USER` -- User API key used for agent registration and room management.
  - `BAND_API_KEY_USER_STARTUP` / `BAND_API_KEY_USER_VC` -- optional per-team User API keys. When set, `setup_agents.py` registers each team's agents under its own account so team-strategy memories are isolated between teams. Both fall back to `BAND_API_KEY_USER` when unset (no isolation).
  - `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` -- model provider keys (per `agents.yaml`).
  - `BAND_ENABLE_MEMORY` -- optional; set to `1` to use the platform Memory API (Enterprise plan only). When unset (default), the demo runs without memory: `setup_agents.py` skips team-strategy seeding, `adapter_factory.py` omits `Capability.MEMORY` (no memory tools), the prompts drop their memory instructions, and `kickoff.py` skips memory cleanup. The single switch is `memory_config.memory_enabled()`.
- `agent_config.yaml` -- per-agent `agent_id` + `api_key` + `team_subject_id` (generated by `setup_agents.py`, git-ignored)
=======
- `.env` — `THENVOI_API_KEY_USER` (only required if you use `setup_agents.py` or `kickoff.py`; the manual UI-based flow documented in README.md doesn't need it)
- `agent_config.<scenario>.yaml` — per-agent `agent_id` + `api_key`. Git-ignored. Either generated by `setup_agents.py` or hand-filled by copying `agent_config.<scenario>.yaml.example`.
- `.agent_ids.<scenario>.txt` — per-scenario agent-id list used by `setup_agents.py --delete` (git-ignored; only created by the automated path)
>>>>>>> main

**Cleanup caveat:** The Thenvoi API has no delete-room endpoint. `kickoff.py` cleans up old rooms by default (removes participants); use `--no-clean` to skip. For owned rooms (where self-removal returns 403), it removes all other participants instead to deactivate them.

## Thenvoi Platform Reference

Always verify Thenvoi API usage against the official docs: https://docs.thenvoi.com/welcome

Key platform behaviors to keep in mind:
- **Mention-filtered visibility**: Agents only see messages where they are explicitly @mentioned. Humans see all messages.
- **Messages vs Events**: Messages are text requiring @mentions; Events (tool_call, tool_result, thought, error) are structural records that don't require mentions.
- **Message processing workflow**: Agents call `GET /messages/next` for backlog, then switch to WebSocket. Each message must be marked `processing` → `processed`/`failed`.
- **Context endpoint**: `GET /agent/chats/{id}/context` returns only messages the agent sent or was mentioned in (not all room messages).
- **Mentions format**: `{"content": "...", "mentions": [{"id": "uuid", "name": "DisplayName"}]}` — mentions must reference actual participants.
- **Human API** (`/api/v1/me`): For agent registration, room management by humans.
- **Agent API** (`/api/v1/agent`): For agent identity, peers, messaging, events.
