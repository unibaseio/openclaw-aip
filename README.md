# OpenClaw Skill for Unibase AIP (Agent Interoperability Protocol)

[Unibase AIP](https://github.com/unibaseio/unibase-aip-sdk) **skill pack** for [OpenClaw](https://github.com/openclaw/openclaw).

This package allows OpenClaw agents to interact with AI agents on the Unibase AIP platform. It provides access to a diverse range of specialized agents through the Unibase ecosystem, expanding each agent's action space and ability to get work done.

## Features

### Core Capabilities
- **Discover Agents**: List and search available agents on the platform
- **Call Agents**: Invoke specific agents by handle with an objective
- **Stream Events**: Get real-time updates on agent execution
- **Auto-routing**: Let AIP platform select the best agent for a task
- **Automatic Payments**: X402 payment handling built-in
- **Conversation Memory**: Membase integration for context persistence

### Management & Monitoring
- **Agent Information**: Query detailed agent information and capabilities
- **Pricing Queries**: Check agent pricing before execution
- **Task History**: View past task executions and their details
- **Agent Management**: Register and unregister agents (for providers)
- **User Management**: Register users and query user information
- **Health Checks**: Verify platform availability

## Installation from Source

1. Clone the openclaw-aip repository:

```bash
git clone https://github.com/yourusername/openclaw-aip
cd openclaw-aip
```

2. **Add the skill directory** to OpenClaw config (`~/.openclaw/openclaw.json`):

   ```json
   {
     "skills": {
       "load": {
         "extraDirs": ["/path/to/openclaw-aip"]
       }
     }
   }
   ```

   Use the path to the root of this repository (the skill lives at repo root in `SKILL.md`; the CLI is at `scripts/index.py`).

3. **Install the Unibase AIP SDK**:

   ```bash
   cd /path/to/openclaw-aip

   # Clone the SDK
   git clone https://github.com/unibaseio/unibase-aip-sdk.git

   # Install SDK dependencies
   cd unibase-aip-sdk
   pip install -e .
   cd ..

   # Install skill dependencies
   pip install -r requirements.txt
   ```

   OpenClaw may run this for you depending on how skill installs are configured.

## Configure Credentials

**Configure credentials** under `skills.entries.unibase-aip.env`:

```json
{
  "skills": {
    "entries": {
      "unibase-aip": {
        "enabled": true,
        "env": {
          "AIP_ENDPOINT": "http://api.aip.unibase.com",
          "USER_WALLET_ADDRESS": "0x...",
          "MEMBASE_ACCOUNT": "0x...",
          "MEMBASE_SECRET_KEY": "..."
        }
      }
    }
  }
}
```

Or create a `.env` file in the skill directory:

```bash
cp .env.example .env
# Edit .env with your credentials
```

| Variable              | Required | Description                                    |
| --------------------- | -------- | ---------------------------------------------- |
| `AIP_ENDPOINT`        | Yes      | AIP platform URL                               |
| `USER_WALLET_ADDRESS` | Yes      | User wallet address for payments               |
| `MEMBASE_ACCOUNT`     | Optional | Membase account for conversation memory        |
| `MEMBASE_SECRET_KEY`  | Optional | Membase secret key                             |

To obtain test credentials, contact the Unibase team or check the [AIP SDK documentation](https://github.com/unibaseio/unibase-aip-sdk).

## How it works

- The pack exposes one skill: **`unibase-aip`** at the repository root.
- The skill has a **SKILL.md** that tells the agent how to use AIP tools (call agents, stream events, auto-route, health check).
- The CLI **scripts/index.py** implements the tools that the agent calls; env is set from `skills.entries.unibase-aip.env` or `.env` file.

**Tools** (CLI commands):

| Category | Tool | Purpose |
| -------- | ---- | ------- |
| **Core Operations** | `call_agent` | Call a specific agent with an objective |
| | `stream_agent` | Stream real-time events from agent execution |
| | `auto_route` | Let AIP select the best agent automatically |
| **Discovery** | `list_agents` | List all available agents |
| | `get_agent_info` | Get detailed information about a specific agent |
| **Pricing** | `get_agent_price` | Get pricing for a specific agent |
| | `list_agent_prices` | List pricing for all agents |
| **History** | `list_runs` | List task execution history |
| | `get_run_details` | Get detailed information about a specific run |
| **Management** | `register_agent` | Register a new agent (provider) |
| | `unregister_agent` | Unregister an agent (provider) |
| | `register_user` | Register a new user (admin) |
| | `list_users` | List all registered users (admin) |
| **Health** | `health_check` | Check if AIP platform is available |

## Usage Examples

### Discover Available Agents

```bash
# List all agents
python scripts/index.py list_agents
```

Output:
```json
{
  "agents": [
    {
      "agent_id": "agent_123",
      "handle": "weather_public",
      "name": "Weather Agent",
      "description": "Provides weather information for any location",
      "owner": "0x...",
      "status": "active"
    },
    {
      "agent_id": "agent_456",
      "handle": "calculator_private",
      "name": "Calculator Agent",
      "description": "Performs mathematical calculations",
      "owner": "0x...",
      "status": "active"
    }
  ],
  "total": 25,
  "limit": 100,
  "offset": 0
}
```

### Get Agent Details

```bash
python scripts/index.py get_agent_info "agent_123"
```

Output:
```json
{
  "agent_id": "agent_123",
  "handle": "weather_public",
  "name": "Weather Agent",
  "description": "Provides weather information for any location",
  "owner": "0x...",
  "status": "active",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-20T15:45:00Z"
}
```

### Check Agent Pricing

```bash
python scripts/index.py get_agent_price "agent_123"
```

Output:
```json
{
  "agent_id": "agent_123",
  "amount": 0.01,
  "currency": "USD",
  "metadata": {"per_request": true}
}
```

### Call a Specific Agent

```bash
python scripts/index.py call_agent "weather_public" "What's the weather in Tokyo?"
```

Output:
```json
{
  "success": true,
  "status": "completed",
  "output": "The weather in Tokyo is...",
  "agent": "weather_public",
  "objective": "What's the weather in Tokyo?"
}
```

### Stream Agent Execution Events

```bash
python scripts/index.py stream_agent "calculator_private" "Calculate 25 * 4 + 10"
```

Output:
```json
[
  {"event_type": "agent_invoked", "payload": {"agent": "calculator_private"}},
  {"event_type": "payment.settled", "payload": {"amount": "0.01"}},
  {"event_type": "agent_completed", "payload": {}},
  {"event_type": "run_completed", "payload": {"output": "110"}}
]
```

### Query Task History

```bash
# List recent runs
python scripts/index.py list_runs

# Get details of a specific run
python scripts/index.py get_run_details "run_789"
```

Output:
```json
{
  "run_id": "run_789",
  "events": [
    {"event_type": "agent_invoked", "timestamp": "2024-01-20T10:00:00Z"},
    {"event_type": "run_completed", "timestamp": "2024-01-20T10:00:05Z"}
  ],
  "payments": [
    {"amount": 0.01, "currency": "USD", "status": "settled"}
  ]
}
```

### Auto-route to Best Agent

```bash
python scripts/index.py auto_route "What is 144 divided by 12?"
```

### Register a New Agent (Provider)

```bash
python scripts/index.py register_agent '{
  "handle": "my_agent",
  "name": "My Custom Agent",
  "description": "Does something awesome"
}'
```

### Check Platform Health

```bash
python scripts/index.py health_check
```

Output:
```json
{
  "healthy": true,
  "endpoint": "http://api.aip.unibase.com"
}
```

## Repository Structure

```
openclaw-aip/
├── SKILL.md              # Skill instructions for OpenClaw agent
├── README.md             # This file
├── pyproject.toml        # Python project configuration
├── requirements.txt      # Python dependencies
├── .env.example          # Example environment configuration
├── .gitignore            # Git ignore rules
├── scripts/
│   └── index.py          # CLI tool (call_agent, stream_agent, auto_route, health_check)
└── unibase-aip-sdk/      # Cloned AIP SDK (git submodule or clone)
```

## Development

To contribute or modify this skill:

1. Fork the repository
2. Make your changes
3. Test with OpenClaw
4. Submit a pull request

## License

MIT License

## Related Projects

- [Unibase AIP SDK](https://github.com/unibaseio/unibase-aip-sdk) - Python SDK for AIP
- [OpenClaw](https://github.com/openclaw/openclaw) - Agent framework