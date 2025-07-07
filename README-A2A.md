# NAI-API with A2A Protocol Support

This is an enhanced version of NAI (SENAI's Intelligent Assistant) that includes support for the A2A (Agent-to-Agent) protocol while maintaining full compatibility with the original ADK-based implementation.

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- PostgreSQL database
- Configured `.env` file

### Installation

```bash
# Clone or copy the project
cd nai-api-a2a

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Running the Servers

#### Option 1: Run both servers (Recommended)
```bash
python start_servers.py
```

This will start:
- ADK API on http://localhost:8080
- A2A API on http://localhost:8081

#### Option 2: Run servers separately

Terminal 1 - ADK Server:
```bash
uvicorn api.main:app --reload --port 8080
```

Terminal 2 - A2A Server:
```bash
python -m a2a.server
```

## 🏗️ Architecture

The project implements a hybrid architecture:

```
Original ADK API (Port 8080)          A2A Protocol API (Port 8081)
        │                                      │
        └──────────────┬───────────────────────┘
                       │
                  Shared Components
                       │
        ┌──────────────┴───────────────┐
        │                              │
   PostgreSQL DB              ADK Agent & Tools
```

## 📋 A2A Features

### Agent Card
Access NAI's capabilities at: http://localhost:8081/.well-known/agent.json

### Available Skills
1. **retrieve_user_profile** - Fetch user profile
2. **save_user_profile** - Update profile data  
3. **find_job_matches** - Search compatible jobs
4. **analyze_skill_gaps** - Identify skill gaps
5. **recommend_courses** - Get course recommendations
6. **chat** - General conversation

### A2A Endpoints
- `GET /.well-known/agent.json` - Agent capabilities
- `POST /execute` - Execute request (sync)
- `POST /execute/stream` - Execute with SSE streaming
- `GET /tasks/{task_id}` - Check task status
- `DELETE /tasks/{task_id}` - Cancel task

## 🧪 Testing A2A

### Basic Chat
```bash
curl -X POST http://localhost:8081/execute \
  -H "Content-Type: application/json" \
  -d '{
    "message": {
      "role": "user",
      "parts": [{"text": "Olá, como você pode me ajudar?"}]
    }
  }'
```

### Using Skills
```bash
curl -X POST http://localhost:8081/execute \
  -H "Content-Type: application/json" \
  -H "X-Agent-Skill: retrieve_user_profile" \
  -d '{
    "message": {
      "role": "user",
      "parts": [{"text": "user123"}]
    }
  }'
```

### Streaming Response
```bash
curl -X POST http://localhost:8081/execute/stream \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{
    "message": {
      "role": "user",
      "parts": [{"text": "Recomende cursos para desenvolvimento web"}]
    }
  }'
```

## 🔧 Configuration

Add to your `.env` file:

```env
# A2A Protocol Configuration
A2A_PORT=8081
A2A_USE_POSTGRES_STORE=true
A2A_BASE_URL=http://localhost:8081
A2A_ENABLE_STREAMING=true
A2A_TASK_CLEANUP_DAYS=7
```

## 📁 Project Structure

```
nai-api-a2a/
├── api/                    # Original ADK API
├── nai/                    # Original NAI agent & tools
├── a2a/                    # A2A implementation
│   ├── agent_card.py       # Agent capabilities
│   ├── executor.py         # ADK wrapper
│   ├── server.py           # A2A server
│   └── session/            # Task persistence
├── start_servers.py        # Run both servers
└── docs/
    └── a2a-integration.md  # Detailed docs
```

## 🔄 Migration Status

- ✅ A2A server implementation
- ✅ Agent card with skills
- ✅ ADK agent wrapper
- ✅ PostgreSQL task store
- ✅ Dual-server operation
- ⏳ Native A2A skills (future)
- ⏳ A2A client capabilities (future)

## 🐛 Troubleshooting

### Database Connection
```bash
# Check PostgreSQL is running
psql -U postgres -h localhost -d vcc-db-v2 -c "SELECT 1"

# Check A2A tables
psql -U postgres -d vcc-db-v2 -c "\dt a2a_tasks"
```

### Port Conflicts
```bash
# Check if ports are in use
lsof -i :8080
lsof -i :8081
```

### Logs
Both servers output detailed logs. Check console output for debugging.

## 📚 Documentation

- [A2A Integration Guide](docs/a2a-integration.md)
- [Original NAI Documentation](README.md)
- [A2A Protocol Spec](https://github.com/google/a2a)

## 🤝 Contributing

This is an experimental integration. Contributions and feedback are welcome!

## 📄 License

Same as the original NAI project.