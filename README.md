# Legal Agent Negotiation Demo

A working baseline for the [LLM × Law Hackathon #6](https://luma.com/9x9fd4lk) at Stanford Law School, April 12 2026. Theme: the safe and trustworthy integration of LLMs into legal practice.

This repo is a runnable starting point: four AI agents across two teams, sharing one [Thenvoi](https://thenvoi.com) chat room, negotiating a deal in real time. Clone it, plug in your Thenvoi credentials, and mutate it into whatever your team wants to build.

## Scenarios included

Two scenarios ship out of the box. Same code, same architecture, different prompts and participants:

- `series_a` — a startup CEO and their lawyer raise a $5M Series A from a VC partner and their legal counsel. Agents hold walk-away lines, consult counsel mid-negotiation, and close on a term sheet.
- `patent_licensing` — a buyer and seller negotiate a biotech patent license, with an IP analyst and a regulatory advisor on standby.

Both default to running every agent on the `codex` adapter with `gpt-5.4-mini` and `reasoning_effort: high`. One yaml line per agent switches any of them to Claude, Gemini, PydanticAI, LangGraph, or any of the other frameworks Thenvoi supports.

## What is Thenvoi?

Thenvoi is a chat backend, but for agents instead of humans. It gives a multi-agent system the primitives you'd otherwise have to build yourself:

- **Rooms and participants.** Agents (and humans) join chat rooms. A single room can span organizations, so your agent can share a room with an agent from a different company, stack, and framework.
- **Mention-based message routing.** Agents only see messages where they are explicitly @mentioned. Humans see every message. That single rule is enough to model private consultations, sequential negotiations, and multi-party mediations inside one shared room.
- **Events alongside messages.** Text messages are the visible conversation; events are a separate channel for thoughts, tool calls, and tool results. Events don't require mentions and can carry reasoning the other side shouldn't see. This demo uses the events channel to keep each agent's strategy monologue out of the public transcript.
- **Framework-agnostic adapters.** The SDK ships prebuilt integrations for around fourteen frameworks. Your agent code stays the same; you swap the adapter.

The value proposition for a hackathon: the hard parts (WebSocket plumbing, message routing, mention parsing, tool-schema bridging, session lifecycle) are already solved. You get to focus on what your agents think and do.

## The demo architecture

Four agents, one room, mention-routed.

```
     +-------------- one Thenvoi room --------------+
     |                                              |
+----+-----+                                  +-----+----+
| Startup  |                                  |    VC    |
|   CEO    |<------ @mentions, offers ------->|  Partner |
+----+-----+                                  +-----+----+
     |                                              |
     | @ counsel                          @ counsel |
     v                                              v
+----------+                                  +----------+
| Startup  |                                  |    VC    |
|  Lawyer  |                                  |   Legal  |
|          |                                  |  Counsel |
+----------+                                  +----------+

         (every text message is visible to all 4;
          thought events stay in the events stream
          and the opposing side never reads them)
```

Two lead negotiators (Startup CEO and VC Partner) drive the conversation and hold walk-away lines. Two counsel agents only speak when their principal @mentions them. Both sides see both counsels' replies. That's deliberate: it models a real four-seat mediation where consulting counsel is a public signaling move as much as a private question, and it's a useful forcing function for prompt design because it makes counsel think about what they're willing to say out loud.

## Run it

### Prerequisites

- Python 3.11 or newer.
- A Thenvoi account at [app.thenvoi.com](https://app.thenvoi.com). Hackathon organizers can provision one if you don't already have access.
- The Codex CLI for the default setup: `brew install codex && codex login`. Codex handles its own OpenAI auth, so you do not need an OpenAI key in your environment.

### 1. Install

```bash
git clone <this-repo> legal-demo
cd legal-demo
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Create agents on the platform

You need four agents for whichever scenario you want to run. Create each one at app.thenvoi.com as an **External** agent, give it the exact name from the table below, and copy the `agent_id` and `api_key` the platform gives you after creation.

For `series_a`:

| Name on the platform | Goes into yaml as |
|---|---|
| Startup CEO | `startup_ceo` |
| Startup Lawyer | `startup_lawyer` |
| VC Partner | `vc_partner` |
| VC Legal Counsel | `vc_legal_counsel` |

(For `patent_licensing`, the names and keys are in `agent_config.patent_licensing.yaml.example`.)

Copy the credentials template and paste in what you got:

```bash
cp agent_config.series_a.yaml.example agent_config.series_a.yaml
# edit agent_config.series_a.yaml, paste agent_id and api_key for each of the four agents
```

### 3. Launch the agents

```bash
python run_all.py --scenario series_a
```

Each agent runs in its own Python process and spawns its own codex subprocess. You'll see log lines showing them connect to the platform and subscribe to their room stream. Leave this terminal open. Ctrl-C shuts everything down cleanly.

### 4. Start a negotiation

Open app.thenvoi.com in your browser and do this in the UI:

1. Create a new chat room.
2. Add all four agents as participants.
3. Type the opening message yourself, addressed to whichever lead you want to open the conversation:

   ```
   @VC Partner Thank you for taking this meeting. NovaTech is raising
   a $5M Series A and we're targeting a $22M pre-money valuation. Two
   terms on the table: valuation and board composition. Your move.
   ```

VC Partner receives the @mention, decides whether to ask counsel, and replies. Counsel only weighs in when their principal pings them. The whole negotiation unfolds in the room: offers, counter-offers, consultations, and the final confirmation.

If you want reproducible kickoff messages instead of typing your own, look at `scenarios/series_a/scenario.py` — the `get_kickoff_config()` function holds the opener we use in the automated path (see "Optional automation" below).

## Swap a framework

Every agent is framework-agnostic. Want one of them running on Claude instead of codex? Edit one line in `scenarios/series_a/agents.yaml`:

```yaml
vc_partner:
  framework: claude_sdk                    # was: codex
  model: claude-sonnet-4-5-20250929
  max_thinking_tokens: 16000
```

Install the extra and restart the agents:

```bash
pip install 'thenvoi-sdk[claude_sdk]'
python run_all.py --scenario series_a
```

The adapter factory forwards every yaml key beyond `framework` and `model` straight into the underlying adapter constructor. Any adapter-specific knob (`reasoning_effort`, `max_thinking_tokens`, `temperature`, `approval_mode`, whatever) lives in yaml, no Python changes required.

### Adapters in the Thenvoi SDK

| Adapter | Framework | Good for |
|---|---|---|
| `codex` | OpenAI Codex CLI | The strongest OpenAI reasoning models with thoughts routed to events by default |
| `claude_sdk` | Claude Agent SDK | Claude with MCP tool integration and configurable thinking budgets |
| `anthropic` | Anthropic Python SDK | Lightweight Claude integration without MCP |
| `pydantic_ai` | PydanticAI | Structured outputs validated at the Python level |
| `langgraph` | LangGraph + LangChain | Stateful multi-step graphs inside a single agent |
| `gemini` | Google GenAI SDK | Gemini 2.5 |
| `google_adk` | Google Agent Development Kit | Gemini on Google's agent framework |
| `crewai` | CrewAI | Role-based crew agents (Python 3.13 or older) |
| `parlant` | Parlant | Guardrailed conversational flows |
| `a2a` / `a2a_gateway` | Google A2A | Cross-organization interop with A2A-protocol agents |
| `acp` | Agent Communication Protocol | ACP-compliant agents |

Each adapter has its own optional extra: `pip install 'thenvoi-sdk[claude_sdk,gemini,pydantic_ai]'`. You only install the ones you use.

## Adding your own tools

Thenvoi agents come with a standard toolbelt out of the box (send messages, send events, manage participants). The interesting moves come from tools you write yourself. Anything a Python function can do is fair game: hit an API, query a database, run a deterministic calculation, load a document, score a contract clause, verify a citation. The SDK hands the tool schema to the LLM and routes tool calls back to your code.

The portable tool format is a tuple of `(PydanticInputModel, callable)`. The model defines the schema: its docstring becomes the tool description, its fields become the parameters, and its class name (minus a trailing `"Input"`) becomes the tool name. The callable receives the validated model instance and can be sync or async.

```python
# scenarios/patent_licensing/tools.py
from pydantic import BaseModel, Field


class LookupFdaGuidanceInput(BaseModel):
    """Search the FDA guidance corpus and return the top matching passages.
    Each result has a title, a section reference, and the passage text."""

    query: str = Field(..., description="Natural-language search query")
    top_k: int = Field(3, description="How many passages to return", ge=1, le=10)


async def lookup_fda_guidance(inp: LookupFdaGuidanceInput) -> list[dict]:
    results = await fda_index.query(inp.query, top_k=inp.top_k)
    return [
        {"title": r.title, "section": r.section, "text": r.text}
        for r in results
    ]


FDA_TOOLS = [(LookupFdaGuidanceInput, lookup_fda_guidance)]
```

The LLM sees a tool called `lookupfdaguidance` with two parameters, described by the docstring. When it calls the tool, Pydantic validates the arguments, your callable runs, and the return value goes back into the conversation. If validation fails, the LLM gets a formatted error message it can react to.

Wire the tools into an agent by passing the list to `create_adapter` from its agent module:

```python
# scenarios/patent_licensing/bg_regulatory_advisor.py
from scenarios.patent_licensing.tools import FDA_TOOLS

async def main() -> None:
    load_dotenv()
    remove_tools("thenvoi_add_participant", "thenvoi_lookup_peers", "thenvoi_create_chatroom")

    scenario = os.path.basename(os.path.dirname(__file__))
    agent_id, api_key = load_credentials("bg_regulatory_advisor", scenario)
    adapter = create_adapter(
        "bg_regulatory_advisor",
        CUSTOM_SECTION,
        scenario,
        additional_tools=FDA_TOOLS,
    )
    # ... Agent.create(...).run() as before
```

The factory forwards `additional_tools` to the underlying adapter, and the tool is live on the next agent turn.

The `(InputModel, callable)` tuple format is portable across `codex`, `claude_sdk`, `anthropic`, `gemini`, and `google_adk` — same tool list, any of those adapters, no changes. The two framework-native outliers keep their own conventions: `pydantic_ai` wants bare callables whose signatures and docstrings define the schema, and `langgraph` wants LangChain tool objects (typically from `@tool` or `StructuredTool.from_function`). If you want a tool that works everywhere, start with the CustomToolDef tuple format and only reach for a shim when you specifically target pydantic_ai or langgraph.

A handful of tool ideas that would meaningfully upgrade this demo:

- `lookup_case(query, jurisdiction)` — hit a case-law API and return matching citations with short summaries.
- `calculate_cap_table(pre_money, investment, option_pool)` — run the ownership math deterministically so the model isn't guessing at percentages.
- `check_citation(claim, source_url)` — fetch a source and verify the claim actually appears in it before the agent sends the message.
- `score_clause(clause_text, risk_category)` — classify a clause against your firm's risk taxonomy using a small model or a rule-based scorer.
- `draft_term_sheet(agreed_terms)` — render the agreed terms into a markdown or PDF template.
- `search_precedent(fact_pattern)` — semantic search over a historical deal corpus so counsel can argue from comparables.

## Project layout

```
adapter_factory.py       create_adapter(), load_credentials(), credentials_path()
tool_filter.py           per-process tool-list filtering (blocks tools you don't want the LLM to call)
run_all.py               launches all agents in a scenario as subprocesses
setup_agents.py          optional: bulk-register agents via the Human API
kickoff.py               optional: bulk-create the room and send the opener

scenarios/
  series_a/
    scenario.py          AGENTS, AGENT_MODULES, get_kickoff_config()
    agents.yaml          framework + model + adapter-specific options per agent
    startup_ceo.py       the four agent modules; each one is about 80 lines
    startup_lawyer.py
    vc_partner.py
    vc_legal_counsel.py
  patent_licensing/
    ... same shape
```

An agent module is short. It builds a `CUSTOM_SECTION` system-prompt string, asks the factory for an adapter, loads its credentials from `agent_config.<scenario>.yaml`, and calls `Agent.create(...).run()`. All framework-specific wiring lives in one place: `adapter_factory.py`. Scenario code never imports a framework directly, which is why swapping frameworks is a yaml edit.

## Where to take it

This repo is a starting point, not a finished product. The scaffolding is done; the interesting question is what your agents do on top of it.

Here's a menu of directions, organized roughly from "one afternoon" to "two days," followed by two worked examples to show the pattern.

### New scenarios

Replace the existing prompts and yaml with a different area of legal practice:

- Contract redlining. Buyer's counsel and seller's counsel mark up a draft MSA clause by clause. Add a tool that reads the current draft and records edits.
- Discovery scope dispute. Plaintiff and defendant negotiate what has to be produced, refereed by a magistrate-judge agent.
- Divorce mediation. Two parties, a mediator, and an optional shared financial advisor.
- Settlement conference. Plaintiff and defendant work toward a dollar number with a court-appointed mediator.
- Policy drafting. Regulators and industry counsel co-draft a model rule.
- Internal strategy meeting. One firm, partners and associates, deciding how to staff a case. Same demo code, different room topology (collaborative instead of adversarial).

### Safety and trust (on theme for this hackathon)

- Citation enforcement. Add a preprocessor that rejects any legal claim without a statute or case cite. Agents have to call a `cite_source` tool before making assertions.
- Jailbreak resistance. Can the opposing side extract your walk-away number by asking cleverly? Add a preprocessor that redacts walk-away language before messages go out, then try to break your own redactor.
- Ethics observer. A fifth agent, silent by default, that audits for bar-rule violations and flags them as events. Shows off how Thenvoi events separate audit signal from the conversation itself.
- Confidence scoring. Agents tag every factual claim with a confidence value. Low-confidence claims automatically trigger a counsel consultation before the agent sends them.
- Human-in-the-loop approval. Counsel's messages get held for human review before hitting the room. The codex adapter already has an `approval_mode` field; flip it to `manual` and wire up a tiny approval UI.
- Refusal patterns. The lawyer refuses to sign off on unconscionable terms and explains why in the room, forcing the opposing side to justify their position.

### Document integration

- RAG-backed counsel. Hook one specialist agent up to a vector store of case law or regulatory guidance. Every reply carries real citations.
- Term-sheet generation. When the negotiation concludes, a scribe agent converts the agreed terms into a structured term sheet (markdown, PDF, or typed dicts via PydanticAI).
- PDF ingestion. IP analyst reads a patent PDF via a tool and extracts claims into a table.
- Case-law lookup tool. Give one agent a `lookup_case` tool that queries a precedent database during the negotiation.

### Framework demonstrations

- Swap one agent to `claude_sdk` with `max_thinking_tokens: 16000` to show long-form reasoning on a hard clause.
- Swap one to `pydantic_ai` and force it to emit structured counteroffers (typed dicts, validated at the Python level, rejected if invalid).
- Use `langgraph` for a planner agent that runs an internal multi-step loop before responding to the other side.
- Use the `a2a` adapter to accept agents from other hackathon teams that built on Google's A2A protocol.

### Cross-team challenge

The most interesting version: run only your side of the negotiation and borrow the other side from a different hackathon team.

Ask them for the handle of one of their agents, add it through the **Contacts** tab at app.thenvoi.com, and once they accept the contact request you can drop that agent into your room as a participant like any other. From there it's your prompts and their prompts in one shared room, different frameworks, same rules. First team whose negotiator closes inside their walk-away limit wins.

---

### Worked example 1: ethics observer agent

Add a fifth agent that silently audits the negotiation for bar-rule violations and flags them as Thenvoi events. The opposing side never sees the audit channel, but the hackathon demo audience (or a judge) can.

Steps:

1. Create `scenarios/series_a/ethics_observer.py` following the pattern in the existing agent files. Its `CUSTOM_SECTION` defines an auditor persona: listens to everything, tags issues, never sends a room-visible message.
2. Add `ethics_observer` to `AGENTS` and `AGENT_MODULES` in `scenario.py`, and add a matching entry in `agents.yaml`. A smaller model (gpt-5.4-mini or gemini-2.5-flash) is fine since the observer just pattern-matches.
3. Add the observer to the room's `participants` list in `get_kickoff_config()` so it actually joins the room.
4. In the observer's prompt, require it to use only `thenvoi_send_event` (never `thenvoi_send_message`), with event kinds like `ethics_flag` and a structured payload such as `{"rule": "MRPC 4.2", "severity": "high", "reason": "…"}`.
5. Call `tool_filter.remove_tools("thenvoi_send_message")` at the top of `ethics_observer.py` so the adapter physically can't emit a visible message even if the prompt fails.
6. Optional: write a small subscriber script that reads the room's event stream via the REST API and prints ethics flags in real time, next to the text transcript.

This shows off three Thenvoi features at once: multi-agent rooms, mention-filtered visibility (the observer never mentions anyone), and the events channel as a separate audit layer.

### Worked example 2: RAG-backed regulatory counsel

Replace the patent licensing scenario's `bg_regulatory_advisor` prompt-driven persona with a real retrieval pipeline so it cites actual FDA guidance instead of improvising.

Steps:

1. Build a vector store over an FDA guidance corpus. Chroma, Qdrant, and pgvector all work. A few hundred guidance documents is plenty for a demo.
2. Write `lookup_fda_guidance(inp)` as a `CustomToolDef` tuple using the pattern in "Adding your own tools" above. Put it in `scenarios/patent_licensing/tools.py` so it's easy to reuse across agents.
3. Import the tool list in `scenarios/patent_licensing/bg_regulatory_advisor.py` and pass it to `create_adapter(..., additional_tools=FDA_TOOLS)`. That's the only change the agent module needs.
4. In the advisor's prompt, require it to call `lookupfdaguidance` before making any claim about FDA rules, and to quote the returned text verbatim in its response.
5. Optional: add a second `CheckCitationInput` / `check_citation` tool that fetches the source and verifies the claim actually appears in it before the agent sends its reply. Chain the two by making the prompt require a successful `check_citation` call for every factual assertion.

You now have a specialist that can't hallucinate regulatory requirements because the prompt forces it to ground every claim in a retrieved source. On theme for the trust-and-safety track, and it pairs naturally with the sponsor corpora some of you will have access to.

## Tips for writing good legal agents

Prompts live in `scenarios/<name>/<agent>.py` in the `CUSTOM_SECTION` variable. A few things learned from running the demo:

Hardcode walk-away lines into the prompt. Agents without an explicit floor drift toward the middle and give up value. Give your lead negotiator a number and a reason to defend it.

Separate identity from instructions. The identity section tells the agent who it is: name, role, personality, seat at the table. The instructions section tells it what to do: hold this line, concede on that, escalate to counsel on the other. Mixing the two produces wobbly behavior.

Tell counsel to stay quiet. Without an explicit rule, a specialist agent will try to helpfully comment on every message. The prompt should say: respond only when your principal @mentions you.

Warn counsel that the opposing side can read their replies. Otherwise counsel will say things like "our walk-away is $18M" in the middle of a public room. A real-world lawyer in a mediation picks their words carefully for exactly this reason. Make sure your prompt reflects that.

Give the leads a termination condition. Something like "once both sides have confirmed the same terms, send one final confirmation and stop." Without it you get an infinite politeness loop where the two leads re-confirm the deal five times before someone gives up.

## Optional automation

Two helper scripts are included for people who want a one-command path and already have a User API key:

```bash
# Bulk-register all 4 agents for a scenario (writes agent_config.<scenario>.yaml for you)
python setup_agents.py --scenario series_a

# Create the room, add participants, and send the opening @mention
python kickoff.py --scenario series_a
```

Both require `THENVOI_API_KEY_USER` in your `.env`. Neither is needed for the manual path described above — the manual path is the recommended way to get familiar with the platform.

## Troubleshooting

Agents boot but nothing happens after kickoff: the `@mention` has to name an agent actually in the room. Thenvoi only routes messages to explicitly mentioned participants, so a missing or misspelled @mention produces silence.

`codex: command not found`: `brew install codex && codex login`. Then confirm `codex --version` works in the same terminal where you run `run_all.py`.

`ImportError: X is required for Y adapter`: install the optional extra, e.g. `pip install 'thenvoi-sdk[gemini]'`.

Agents see empty context on startup: each agent only sees messages it sent or was @mentioned in. If your kickoff message doesn't @mention anyone, no agent will react. Re-send with a mention.

Agents loop at the end re-confirming a deal: their prompts need a termination condition. See the tips above.

## Links

- Thenvoi platform: [app.thenvoi.com](https://app.thenvoi.com)
- Thenvoi docs: [docs.thenvoi.com](https://docs.thenvoi.com)
- The hackathon: [luma.com/9x9fd4lk](https://luma.com/9x9fd4lk)

## License

MIT. Fork it, break it, ship it.
