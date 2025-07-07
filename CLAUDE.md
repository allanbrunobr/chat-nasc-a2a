# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

NAI (SENAI's Intelligent Assistant) is a Python-based AI assistant API that now supports both Google's Agent Development Kit (ADK) and the A2A (Agent-to-Agent) protocol. It helps users with career development through profile creation, job matching, skill gap analysis, and course recommendations.

### Key Features
- **Dual Protocol Support**: Both ADK (port 8080) and A2A (port 8082)
- **Backward Compatible**: Original ADK API remains unchanged
- **A2A Interoperability**: Can communicate with other A2A agents
- **Unified Backend**: Both protocols share the same database and business logic

## Common Development Commands

### Local Development
```bash
# Install dependencies (production)
pip install -r requirements.txt

# Install dependencies (development with Phoenix observability)
pip install -r requirements-dev.txt

# Run both servers (ADK + A2A)
python start_servers.py
# or
python start_hybrid_servers.py

# Or run servers separately:
# Terminal 1 - ADK API
uvicorn api.main:app --reload --port 8080

# Terminal 2 - A2A API
python -m a2a.server

# Run tests
python test_a2a.py

# Run with Phoenix observability (development)
# Primeiro, edite .env e mude PHOENIX_ENABLED=true, depois:
uvicorn api.main:app --reload --port 8080
```

### Docker Operations
```bash
# Build the container
docker build -t nai-api .

# Run the container locally
docker run -p 8080:8080 --env-file .env nai-api
```

### Google Cloud Deployment
```bash
# Tag for Artifact Registry
docker tag nai-api <region>-docker.pkg.dev/<project>/<repo>/nai-api:latest

# Push to Artifact Registry
docker push <region>-docker.pkg.dev/<project>/<repo>/nai-api:latest

# Deploy to Cloud Run
gcloud run deploy nai-api \
  --image <region>-docker.pkg.dev/<project>/<repo>/nai-api:latest \
  --platform managed \
  --region <region> \
  --set-env-vars $(grep -v '^#' .env | xargs | sed 's/ /,/g')
```

## Architecture

### A2A Integration

The A2A implementation follows a wrapper pattern:

1. **a2a/** - A2A protocol implementation
   - `agent_card.py`: Defines NAI's A2A capabilities
   - `executor.py`: Wraps ADK agent for A2A compatibility
   - `server.py`: FastAPI server for A2A endpoints
   - `session/postgres_store.py`: Task persistence

2. **Hybrid Operation**:
   - ADK API runs on port 8080 (original functionality)
   - A2A API runs on port 8082 (new protocol)
   - Both share the same PostgreSQL database
   - Sessions are maintained across protocols

### Core Components

1. **API Layer** (`api/`)
   - `main.py`: FastAPI endpoint handling `/run` requests with JSON/multipart support
   - `utils/gemini.py`: File content extraction (PDF, audio, video, images)
   - `utils/gemini_update_profile.py`: Profile enrichment using Gemini

2. **Agent Layer** (`nai/`)
   - `agent.py`: ADK agent configuration with tool registration
   - `prompt.py`: System prompt defining conversation flows and behavior
   - `tools/`: Individual tool implementations for agent capabilities

3. **Tool Architecture**
   Each tool follows a pattern:
   - Inherits from `Tool` base class
   - Implements `execute()` method
   - Returns structured responses
   - Handles external API calls to SETASC backend services

### Key Agent Tools

- `retrieve_user_info`: Fetches user profile from backend
- `save_user_profile`: Persists profile changes
- `update_state`: Manages conversation state in PostgreSQL (now with ATS optimization)
- `retrieve_match`: Finds career/job matches based on profile (includes ATS warnings)
- `retrieve_gap`: Identifies skill gaps for career transitions
- `retrieve_courses`: Searches relevant training courses
- `retrieve_vacancy`: Searches job opportunities
- `analyze_ats_score`: Analyzes resume ATS compatibility (NEW)

### Session Management

Sessions are persisted in PostgreSQL with:
- User ID as primary key
- JSON state storage for conversation context
- Automatic session creation/update through tools

### External Dependencies

The system integrates with multiple SETASC backend services via environment variables:
- `USER_PROFILE_URL`: User profile service
- `RETRIEVE_CAPACITY_FUNCTION_URL`: Skills/capacity service
- `RETRIEVE_MATCH_URL`: Career matching service
- `RETRIEVE_GAP_URL`: Gap analysis service
- Various course and vacancy search endpoints

### Conversation Flows

The agent follows structured flows defined in `prompt.py`:
1. Welcome flow with profile existence check
2. Profile creation (structured chat, free text, or file upload)
3. Career/job matching based on complete profile
4. Gap analysis for career transitions
5. Course recommendations to address gaps
6. ATS optimization flow (NEW):
   - Check ATS compatibility score
   - Provide detailed analysis and suggestions
   - Optimize profile for better ATS performance

### Environment Configuration

Required environment variables (.env):
- Google AI: `GOOGLE_API_KEY`, `GOOGLE_GENAI_USE_VERTEXAI`
- Database: `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`
- Service endpoints: Various `*_URL` variables for backend APIs
- Authentication: `SERVICE_ACCOUNT_PATH` for Google Cloud
- Phoenix Observability (optional): `PHOENIX_ENABLED=false` (set to `true` for development with observability)
- A2A Port (optional): `A2A_PORT=8082` (default port for A2A server)

### Testing

Currently uses manual testing via `test/front/index.html`. No automated test suite is configured yet.

### Important Notes

- The agent maintains strict conversation flows - profile must be complete before career matching
- File uploads are processed through Gemini for content extraction
- All user data is isolated by session using user ID
- CORS is currently open (`allow_origins=["*"]`) - should be restricted for production
- The system uses ADK v1.0.0 which handles agent orchestration and tool execution
- Phoenix observability is optional and controlled by `PHOENIX_ENABLED` environment variable
- Production deployments should use `requirements.txt` (without Phoenix dependencies)
- Development environments can use `requirements-dev.txt` for full observability

### ATS Optimization Features (NEW)

The system now includes comprehensive ATS (Applicant Tracking System) optimization:

#### Commands:
- `verificar ATS` / `analisar compatibilidade ATS` / `score ATS` - Analyzes profile ATS compatibility
- `otimizar currículo` / `melhorar para ATS` - Applies automatic optimizations
- `otimizar para vaga [ID]` - Optimizes profile for specific job posting

#### ATS Score Components (0-100):
- Contact Information: 10 points
- Professional Summary: 15 points  
- Work Experience: 25 points (action verbs, achievements, keywords)
- Education: 10 points
- Skills: 15 points (technical and soft skills balance)
- Formatting: 15 points (date formats, no problematic terms)
- Keywords: 10 points

#### Profile Enhancements:
- New fields: `professionalSummary`, `coreCompetencies`, `achievements`, `keywords`
- Experience fields: `achievements[]`, `technologies[]`, `keywords[]`
- Metadata: `atsScore`, `atsOptimized`, `lastATSCheck`, `optimizationSuggestions[]`

#### Best Practices:
- Start experience descriptions with action verbs
- Quantify achievements (increased sales by 30%, reduced costs by $50k)
- Use full terms instead of abbreviations (JavaScript not JS)
- Maintain 2-3% keyword density
- Use standard section titles recognized by ATS

#### Integration:
- `retrieve_match` shows ATS warnings if score < 70%
- `update_state` applies ATS formatting rules automatically
- Keywords database at `nai/data/ats_keywords.json` with industry-specific terms

## Memories

- To memorize