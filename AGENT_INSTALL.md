# AGENT_INSTALL.md

**For AI agents.** You are helping a developer get set up with the [legal-demo](https://github.com/thenvoi/legal-demo) on Thenvoi. Follow these steps in order. Run commands yourself where indicated. When you need input from the user, use `AskUserTool` / `request_user_input` / the appropriate tool for your harness to ask questions and present options.

---

## Step 1: Sign up for Thenvoi

Ask the user (via your input tool): "Do you already have a Thenvoi account at app.thenvoi.com?"

- If yes, skip to Step 2.
- If no: "Go to https://www.thenvoi.com and click 'Get started for free'. Sign up with your email. Come back once you're in."

---

## Step 2: Get a User API key

Tell the user: "We need a User API key. In the app go to:

**app.thenvoi.com → your name (top-left) → Settings → REST API Keys → Create New API Key**

Give it any name. Copy the key it shows you."

Ask them to paste it. Write it into `.env`:

```
THENVOI_API_KEY_USER=their_key_here
```

---

## Step 3: Two paths

Ask (via your input tool): **"Do you want to run the built-in demo first, or go straight to building your idea?"**

Options:
- Run the demo
- Build my idea

- If **run the demo** → follow [Path A](#path-a-run-the-demo)
- If **build their idea** → follow [Path B](#path-b-build-the-idea)

---

## Path A: Run the demo

### A1. Get the repo

Check the current directory:

```bash
ls -la
```

If `run_all.py` and `scenarios/` are present, the repo is already here. Skip to A2.

Otherwise:

```bash
git clone https://github.com/thenvoi/legal-demo .
```

### A2. Install dependencies

Run this — it uses `uv` if available, otherwise falls back to a standard venv:

```bash
if command -v uv &>/dev/null; then
  uv venv .venv && source .venv/bin/activate && uv pip install -r requirements.txt
else
  python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt
fi
```

If Python itself is missing, tell the user they need Python 3.11+ and point them to python.org.

### A3. Detect what model access they have

Run these checks silently before asking the user anything. You're building a picture of what's already available so you can present relevant options, not a blank menu.

```bash
# CLIs installed
which codex 2>/dev/null && echo "codex: YES" || echo "codex: NO"
which claude 2>/dev/null && echo "claude: YES" || echo "claude: NO"
which ollama 2>/dev/null && echo "ollama: YES" || echo "ollama: NO"

# API keys in the environment
echo "OPENAI_API_KEY: ${OPENAI_API_KEY:+SET}"
echo "ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY:+SET}"
echo "GEMINI_API_KEY: ${GEMINI_API_KEY:+SET}"

# Existing .env
cat .env 2>/dev/null || echo "(no .env yet)"

# Existing agent credentials (agents already registered on Thenvoi)
ls agent_config.*.yaml 2>/dev/null || echo "(no agent configs found)"

# Existing scenarios
ls scenarios/ 2>/dev/null
```

If any `agent_config.<scenario>.yaml` files exist and are non-empty, note this — the user may already have agents registered on Thenvoi and can skip the agent creation step for that scenario.

Based on what you found, present the relevant options via your input tool as **multi-select** (they can pick more than one — the demo supports mixing frameworks across agents). Always include "Other" so they can type a custom answer. Only pre-select options you actually detected:

| Option | Show if... |
|---|---|
| OpenAI API key | `OPENAI_API_KEY` is set, or they might have one |
| Codex CLI | `codex` is installed |
| Claude subscription | `claude` is installed |
| Gemini API key | `GEMINI_API_KEY` is set, or they might have one |
| Anthropic API key | `ANTHROPIC_API_KEY` is set |
| Local model (Ollama) | `ollama` is installed |
| Other | always include — let them type a custom answer |

If they pick multiple, assign different frameworks to different agents in `agents.yaml`. Each agent can use a different framework.

Once they pick one:

- **OpenAI API key:** if not already in `.env`, ask them to paste it. Write `OPENAI_API_KEY=...` to `.env`. No changes to `agents.yaml` needed.

- **Codex CLI:** confirm `codex login` has been run. Swap all four agents in `scenarios/series_a/agents.yaml` to `framework: codex` and `model: gpt-5.4-mini`. No API key needed.

- **Claude subscription:** confirm `claude` CLI is logged in. Swap agents to `framework: claude_sdk` and `model: claude-sonnet-4-6`. Run `pip install 'thenvoi-sdk[claude_sdk]'`.

- **Gemini:** if not already set, ask for `GEMINI_API_KEY` and write to `.env`. Swap agents to `framework: gemini` and `model: gemini-2.5-flash`. Run `pip install 'thenvoi-sdk[gemini]'`.

- **Anthropic API key:** if not already set, ask for `ANTHROPIC_API_KEY` and write to `.env`. Swap agents to `framework: anthropic` and `model: claude-sonnet-4-6`.

- **Local model:** ask which model they have running in Ollama (`ollama list`). Write to `.env`:
  ```
  OPENAI_BASE_URL=http://localhost:11434/v1
  OPENAI_API_KEY=ollama
  ```
  Swap agents to `framework: langgraph` and their model name.

### A4. Create the four agents on Thenvoi

Run the automated setup:

```bash
python setup_agents.py --scenario series_a
```

If it succeeds, you'll see four agent IDs printed and `agent_config.series_a.yaml` is written automatically. Skip to A5.

**If setup_agents.py fails**, guide the user through manual creation. For each of the four agents below:

1. Go to **app.thenvoi.com/agents** → "Create new agent"
2. Enter the Agent Name exactly as shown
3. Check **"External Agent (brings its own reasoning loop)"**
4. Click **"Create External Agent"**
5. **Copy the API key — it is shown only once.** If they miss it, they can click "Regenerate API Key" on the agent's detail page
6. Copy the Agent UUID shown at the top of the agent's detail page

Agents to create:

| Agent Name | Config key |
|---|---|
| Startup CEO | `startup_ceo` |
| Startup Lawyer | `startup_lawyer` |
| VC Partner | `vc_partner` |
| VC Legal Counsel | `vc_legal_counsel` |

Ask for each `agent_id` and `api_key` via your input tool (one agent at a time is fine). Then write them to `agent_config.series_a.yaml`:

```bash
cp agent_config.series_a.yaml.example agent_config.series_a.yaml
```

Fill in:

```yaml
startup_ceo:
  agent_id: "uuid-here"
  api_key: "key-here"

startup_lawyer:
  agent_id: "uuid-here"
  api_key: "key-here"

vc_partner:
  agent_id: "uuid-here"
  api_key: "key-here"

vc_legal_counsel:
  agent_id: "uuid-here"
  api_key: "key-here"
```

### A5. Start the agents

```bash
python run_all.py --scenario series_a
```

You should see four lines like `[startup_ceo] Startup CEO agent is online.`

**Common errors:**
- `KeyError: 'startup_ceo'` — config file has wrong key names or is missing
- `ImportError` — run `pip install 'thenvoi-sdk[framework_name]'`
- Auth error — check the `.env` key for the chosen framework

### A6. Start a negotiation

Tell the user: "Open app.thenvoi.com, create a new chat room, add all four agents as participants, then send this opening message:"

```
@VC Partner Thank you for taking this meeting. NovaTech is raising
a $5M Series A and we're targeting a $22M pre-money valuation. Two
terms on the table: valuation and board composition. Your move.
```

Watch the agents negotiate in real time. VC Partner and Startup CEO drive the conversation; the lawyers only speak when @mentioned by their principal.

Once it's running, ask (via your input tool): **"What's your idea?"** Then follow Path B from B1 onward to help them build it.

---

## Path B: Build the idea

### B1. Understand the idea

Ask (via your input tool): **"What do you want to build? Describe the idea."**

While they answer, or just after, look at the repo structure: `scenarios/`, the agent modules, `adapter_factory.py`, the README. Think about how the idea maps onto the architecture:

- New conversation scenario between named roles → new `scenarios/<name>/` folder, each agent ~80 lines
- Needs external data (case law, contracts, FDA guidance) → `CustomToolDef` tuples or an MCP server
- Needs a silent auditor → fifth agent that only emits events, never sends messages
- Needs a different number of agents → adjust the scenario

Give them specific, honest feedback on what it needs. Work with them to name each agent and define their role.

### B2. Get the repo and dependencies

Same as A1 and A2. Do these before moving on.

### B3. Detect what model access they have

Same as A3 — run the checks first, then present what's actually available. Also check for any existing agent configs or scenarios the user might already have set up, so you don't duplicate work.

### B4. Figure out which agents they need

Ask (via your input tool): **"How many agents do you need, and what are their roles?"**

Get concrete answers: names, who they talk to, whether they're a lead or a specialist, what tools they'll need. This drives the number of agents they create in the next step.

### B5. Create agents on Thenvoi

For each agent, guide the user through:

1. Go to **app.thenvoi.com/agents** → "Create new agent"
2. Enter the Agent Name
3. Write a short Description
4. Check **"External Agent (brings its own reasoning loop)"**
5. Click **"Create External Agent"**
6. **Copy the API key immediately — shown only once.** Regenerate from the agent detail page if missed
7. Copy the Agent UUID from the detail page

Ask for each `agent_id` and `api_key` (via your input tool). Write them into a new credentials file:

```bash
mkdir -p scenarios/your_scenario_name
```

Create `agent_config.your_scenario_name.yaml`:

```yaml
agent_one:
  agent_id: "uuid-here"
  api_key: "key-here"

agent_two:
  agent_id: "uuid-here"
  api_key: "key-here"
```

### B6. Scaffold and build

Create the scenario folder and implement:

1. `scenarios/your_scenario_name/scenario.py` — following `scenarios/series_a/scenario.py` as the template: `AGENTS`, `AGENT_MODULES`, `get_kickoff_config()`
2. `scenarios/your_scenario_name/agents.yaml` — framework and model per agent
3. One module per agent (~80 lines each) — following `scenarios/series_a/startup_ceo.py`
4. `scenarios/your_scenario_name/tools.py` if they need custom tools

Write the code now. Don't stop to ask permission at each file — they said they want to build it.

### B7. Tell them how to run it

Once the code is in place:

```bash
# Terminal 1 — start the agents
python run_all.py --scenario your_scenario_name

# Terminal 2 — optional automated kickoff (if you've implemented kickoff.py support)
python kickoff.py --scenario your_scenario_name
```

If kickoff isn't implemented: tell them to create a room manually at app.thenvoi.com, add their agents as participants, and send an opening message @mentioning a lead agent.

To register and tear down agents automatically (requires `THENVOI_API_KEY_USER` in `.env`):

```bash
python setup_agents.py --scenario your_scenario_name
python setup_agents.py --delete --scenario your_scenario_name
```
