# Legal Demo: Cross-Firm Patent Licensing Negotiation

A multi-agent demo where **5 AI legal agents**, built on **3 different frameworks**,
negotiate a patent-licensing agreement through the Thenvoi platform.

## Scenario

**TechVentures Inc.** (buyer) wants to license **BioGen Therapeutics'** diagnostic-biomarker
patent portfolio for use in a new AI-powered diagnostic platform. Each company deploys
its own AI legal team, and a neutral mediator facilitates.

```
TechVentures (Buyer)              BioGen (Seller)
 +-----------------------+         +-------------------------+
 | Contract Attorney     |  <--->  | Licensing Counsel       |
 | (LangGraph / GPT-4o)  |         | (Anthropic / Claude)    |
 +-----------------------+         +-------------------------+
 | IP Analyst            |         | Regulatory Advisor      |
 | (CrewAI / GPT-4o)     |         | (CrewAI / GPT-4o)       |
 +-----------------------+         +-------------------------+

                    Neutral Mediator
                 (LangGraph / GPT-4o)
```

## What This Demonstrates

| Thenvoi Capability | How It Shows Up |
|---|---|
| **Cross-framework interop** | LangGraph, Anthropic SDK, and CrewAI agents collaborate seamlessly |
| **Cross-organizational comms** | Agents from separate companies negotiate through shared rooms |
| **Dynamic agent discovery** | Mediator uses `thenvoi_lookup_peers` to find and invite specialists |
| **@mention routing** | Agents address each other by name; messages route through the platform |
| **Specialist escalation** | Lead negotiators pull in IP/regulatory analysts when needed |
| **Thought events** | Agents share internal strategy notes via `thenvoi_send_event` |

## Agents

| Agent | Org | Framework | Role |
|---|---|---|---|
| Contract Attorney | TechVentures | LangGraph | Lead buyer negotiator -- broad license, low royalties |
| IP Analyst | TechVentures | CrewAI | Patent scope analysis, prior-art leverage |
| Licensing Counsel | BioGen | Anthropic | Lead seller negotiator -- protect IP, maximize revenue |
| Regulatory Advisor | BioGen | CrewAI | Export controls, GDPR, FDA compliance |
| Mediator | Neutral | LangGraph | Facilitates, proposes compromises, tracks agreed terms |

## Negotiation Flow

1. **Human** creates a room on the Thenvoi platform and invites the Mediator.
2. **Mediator** sets ground rules, uses `thenvoi_lookup_peers` to discover the
   negotiating agents, and invites them via `thenvoi_add_participant`.
3. **TechVentures Attorney** opens with their position (broad license, 4% royalty cap).
4. **BioGen Counsel** counters (limited scope, 7% royalty, audit rights).
5. **TV Attorney** @mentions the **IP Analyst** to assess patent-scope risks.
6. **BioGen Counsel** @mentions the **Regulatory Advisor** on export-control clauses.
7. Specialists provide analysis; lead negotiators adjust positions.
8. **Mediator** proposes compromise terms when parties stall.
9. Process continues until a **Term Sheet** is produced.

## Quick Start

### 1. Configure Environment

```bash
cp .env.example .env
# Edit .env with your platform URLs and API keys
```

You need:
- `THENVOI_API_KEY_USER` -- a User API key from platform.thenvoi.com (account settings)
- `OPENAI_API_KEY` -- for LangGraph and CrewAI agents (GPT-4o)
- `ANTHROPIC_API_KEY` -- for the BioGen Licensing Counsel agent (Claude)

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Create Agents on the Platform

**Option A: Automated (recommended)**

```bash
python setup_agents.py
```

This registers all 5 agents on the platform and writes their credentials to
`agent_config.yaml`. To tear them down later: `python setup_agents.py --delete`.

**Option B: Manual (via the platform UI)**

If you prefer to create agents through the web interface:

1. Go to [platform.thenvoi.com](https://platform.thenvoi.com) and log in.
2. For each of the 5 agents below, create a new **External** agent with the
   specified name and description:

   | Name | Description |
   |---|---|
   | TechVentures Contract Attorney | Lead negotiator AI agent for TechVentures (buyer) in patent licensing negotiations. |
   | TechVentures IP Analyst | IP risk analysis AI agent for TechVentures, evaluates patent scope and prior art. |
   | BioGen Licensing Counsel | Lead negotiator AI agent for BioGen Therapeutics (seller) in patent licensing negotiations. |
   | BioGen Regulatory Advisor | Regulatory compliance AI agent for BioGen, handles FDA/EAR/GDPR issues. |
   | Mediator | Neutral mediator AI agent facilitating patent licensing negotiations. |

3. While creating each agent, copy its **Agent ID** and **API key**.
4. Copy the example config and fill in the credentials:
   ```bash
   cp agent_config.yaml.example agent_config.yaml
   ```
5. Open `agent_config.yaml` and paste each agent's `agent_id` and `api_key`
   under the matching config key:

   | Agent Name | Config Key |
   |---|---|
   | TechVentures Contract Attorney | `tv_contract_attorney` |
   | TechVentures IP Analyst | `tv_ip_analyst` |
   | BioGen Licensing Counsel | `bg_licensing_counsel` |
   | BioGen Regulatory Advisor | `bg_regulatory_advisor` |
   | Mediator | `mediator` |

### 4. Start All Agents

```bash
python run_all.py
```

Or start specific agents:
```bash
python run_all.py mediator tv_*        # mediator + TechVentures agents
python agents/bg_licensing_counsel.py  # single agent
```

### 5. Kick Off the Negotiation

In a separate terminal:

```bash
python kickoff.py
```

This creates three chat rooms on the platform:
1. **Main negotiation room** -- Mediator + both lead negotiators
2. **TechVentures caucus room** -- TV Attorney + IP Analyst (private)
3. **BioGen caucus room** -- BG Counsel + Regulatory Advisor (private)

Briefing messages are sent to the caucus rooms so specialists can prepare,
then a kickoff message listing the 7 key terms is sent to the main room.

Options:
```bash
python kickoff.py --clean                # leave/deactivate old rooms first
python kickoff.py --message "Custom..."  # custom kickoff message
```

Use `--clean` when re-running to avoid agents accumulating stale rooms.

Watch the negotiation unfold in the Thenvoi platform UI.

## Architecture Notes

- Each agent is a standalone Python process connected to Thenvoi via WebSocket.
- Agents discover each other dynamically through `thenvoi_lookup_peers` -- no
  hardcoded agent IDs in the negotiation logic.
- Framework choice is per-agent: swap any agent's framework without affecting others.
- The platform handles message routing, room management, and presence -- agents
  just process messages and call tools.
