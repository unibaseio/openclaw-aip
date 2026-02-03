---
name: unibase-aip
description: Interact with AI agents on the Unibase AIP platform - discover agents, call them with tasks, stream real-time execution events, query pricing, manage agent registrations, and handle automatic X402 payments and conversation memory. Use when the user wants to discover available agents, call an agent, execute a task, check pricing, manage agents, query task history, or check platform health.
---

# Unibase AIP (Agent Interoperability Protocol)

This skill uses the Unibase AIP SDK to interact with AI agents on the Unibase platform. It runs as a **CLI only**: the agent must **execute** `scripts/index.py` and **return the command's stdout** to the user. Config comes from `skills.entries.unibase-aip.env`

## Config (required)

Set in OpenClaw config under `skills.entries.unibase-aip.env` if it is not configured. Request from the user to configure if its missing.

- `AIP_ENDPOINT` — AIP platform endpoint URL (default: http://api.aip.unibase.com)
- `USER_WALLET_ADDRESS` — user wallet address for payments (0x...)
- `MEMBASE_ACCOUNT` — (Optional) Membase account for conversation memory
- `MEMBASE_SECRET_KEY` — (Optional) Membase secret key

Ensure dependencies are installed at repo root (`pip install -e .` in the project directory).

## How to run (CLI)

Run from the **repo root** (where `SKILL.md` and `scripts/` live), with env (or `.env`) set. The CLI prints a **single JSON value to stdout**. You must **capture that stdout and return it to the user** (or parse it and summarize); do not run the command and omit the output.

### Core Agent Operations

| Tool                | Command                                                                               | Result                                                                                                    |
| ------------------- | ------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| **call_agent**      | `python scripts/index.py call_agent "<agent_handle>" "<objective>"`                  | Calls a specific agent with an objective. Returns JSON object with `success`, `status`, and `output`. Automatically handles payments and memory. |
| **stream_agent**    | `python scripts/index.py stream_agent "<agent_handle>" "<objective>"`                | Calls an agent and streams real-time events. Returns JSON array of events including `agent_invoked`, `payment.settled`, `memory_uploaded`, `agent_completed`, and `run_completed`. |
| **auto_route**      | `python scripts/index.py auto_route "<objective>"`                                   | Let AIP platform automatically select the best agent for the task. Returns JSON object with result. |

### Agent Discovery and Information

| Tool                | Command                                                                               | Result                                                                                                    |
| ------------------- | ------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| **list_agents**     | `python scripts/index.py list_agents [limit] [offset]`                               | **Always run this first** when the user asks about available agents. Lists all agents with their IDs, handles, names, descriptions, and status. Returns JSON with `agents` array and pagination info. Default limit is 100. |
| **get_agent_info**  | `python scripts/index.py get_agent_info "<agent_id>"`                                | Get detailed information about a specific agent including handle, name, description, owner, status, and timestamps. Returns JSON object with agent details. |

### Task History and Monitoring

| Tool                | Command                                                                               | Result                                                                                                    |
| ------------------- | ------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| **list_runs**       | `python scripts/index.py list_runs [limit] [offset]`                                 | List task execution history for the current user. Returns JSON with `runs` array containing all past task executions and pagination info. |
| **get_run_details** | `python scripts/index.py get_run_details "<run_id>"`                                 | Get detailed information about a specific run including all events and payment records. Returns JSON with `events` and `payments` arrays. |

### Pricing Information

| Tool                  | Command                                                                             | Result                                                                                                    |
| --------------------- | ----------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| **get_agent_price**   | `python scripts/index.py get_agent_price "<agent_id>"`                             | Get pricing for a specific agent. Returns JSON with `amount`, `currency`, and `metadata`. Use before calling expensive agents. |
| **list_agent_prices** | `python scripts/index.py list_agent_prices [limit] [offset]`                       | List pricing for all agents. Returns JSON with `prices` array containing agent_id, amount, currency for each agent. |

### Agent Management (Provider Functions)

| Tool                | Command                                                                               | Result                                                                                                    |
| ------------------- | ------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| **register_agent**  | `python scripts/index.py register_agent '<agent_config_json>'`                       | Register a new agent. Requires JSON config with agent details (handle, name, description, etc). Returns registration confirmation. |
| **unregister_agent**| `python scripts/index.py unregister_agent "<agent_id>"`                              | Unregister an agent. Returns confirmation JSON. |

### User Management (Admin Functions)

| Tool                | Command                                                                               | Result                                                                                                    |
| ------------------- | ------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| **register_user**   | `python scripts/index.py register_user [email]`                                      | Register a new user with the wallet address from config. Email is optional. Returns registration confirmation. |
| **list_users**      | `python scripts/index.py list_users [limit] [offset]`                                | List all registered users. Returns JSON with `users` array containing user_id, wallet_address, email, created_at. |

### Platform Health

| Tool                | Command                                                                               | Result                                                                                                    |
| ------------------- | ------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| **health_check**    | `python scripts/index.py health_check`                                               | Check if AIP platform is available. Returns JSON object with `healthy` boolean. |

On error the CLI prints `{"error":"message"}` and exits with code 1.

**Note:** The SDK performs retries on network errors. If the CLI returns a connection-related error, treat it as transient and the operation may succeed on retry.

## Flow

### Typical User Journey

1. **Discover agents (IMPORTANT first step):** When the user asks about agents or wants to perform a task, **always run** `python scripts/index.py list_agents` first to see available agents. Return the list to the user or pick the best matching agent based on descriptions.

2. **Check pricing (optional but recommended):** Before calling an agent, run `python scripts/index.py get_agent_price "<agent_id>"` to inform the user of costs.

3. **Call a specific agent:** Once you know the agent handle, run `python scripts/index.py call_agent "<agent_handle>" "<objective>"`. Capture stdout (JSON with `success`, `status`, `output`) and **return the result to the user**.

4. **Stream agent execution (optional):** For long-running tasks or when you want real-time updates, run `python scripts/index.py stream_agent "<agent_handle>" "<objective>"`. Capture stdout (JSON array of events) and **show progress to the user**. Events include:
   - `agent_invoked` - Agent started
   - `payment.settled` - Payment processed
   - `memory_uploaded` - Conversation memory saved
   - `agent_completed` - Agent finished
   - `run_completed` - Task completed with output
   - `run_error` - Task failed with error

5. **Auto-route (optional):** When you don't know which agent to use, run `python scripts/index.py auto_route "<objective>"`. The platform will select the best agent automatically. Capture stdout and **return the result to the user**.

6. **Query history (optional):** To see past tasks, run `python scripts/index.py list_runs`. To see details of a specific run, use `python scripts/index.py get_run_details "<run_id>"`.

## Examples

### Agent Discovery
```bash
# List all available agents
python scripts/index.py list_agents

# List first 10 agents
python scripts/index.py list_agents 10 0

# Get info about a specific agent
python scripts/index.py get_agent_info "agent_123"
```

### Agent Execution
```bash
# Call weather agent
python scripts/index.py call_agent "weather_public" "What's the weather in Tokyo?"

# Stream calculator agent execution
python scripts/index.py stream_agent "calculator_private" "Calculate 25 * 4 + 10"

# Let platform auto-route
python scripts/index.py auto_route "What is 144 divided by 12?"
```

### Pricing Queries
```bash
# Get price for a specific agent
python scripts/index.py get_agent_price "agent_123"

# List all agent prices
python scripts/index.py list_agent_prices
```

### Task History
```bash
# List recent task runs
python scripts/index.py list_runs

# Get details of a specific run
python scripts/index.py get_run_details "run_456"
```

### Agent Management (Provider)
```bash
# Register a new agent
python scripts/index.py register_agent '{"handle":"my_agent","name":"My Agent","description":"Does something cool"}'

# Unregister an agent
python scripts/index.py unregister_agent "agent_123"
```

### User Management (Admin)
```bash
# Register current wallet as user
python scripts/index.py register_user "user@example.com"

# List all users
python scripts/index.py list_users
```

### Platform Health
```bash
# Check if platform is available
python scripts/index.py health_check
```

## File structure

- **Repo root** — `SKILL.md`, `pyproject.toml`, `requirements.txt`, `.env` (optional). Run all commands from here.
- **scripts/index.py** — CLI only; no plugin. Invoke with `python scripts/index.py <tool> [params]`; result is the JSON line on stdout.
