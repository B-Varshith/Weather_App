# Weather Advisory Bot

A policy-controlled conversational chatbot that provides safety recommendations for outdoor activities based on **live weather data** and **Standard Operating Procedures (SOPs)**.

```
Weather API → Structured Weather Facts → SOP Engine → Decision → LLM Response Composer
```

> **Core Principle:** The LLM never decides safety advice. Decisions are made deterministically by the SOP engine using real weather data. The LLM only extracts intent and composes natural-language responses.

---

## Architecture

```
START
  │
  ▼
classify_intent  (LLM: extract activity, location, time, user_group)
  │
  ▼
resolve_location  (Open-Meteo Geocoding API)
  │
  ├── failure ──► location_failure ──► END
  │
  ▼
fetch_weather  (Open-Meteo Forecast API)
  │
  ├── failure ──► weather_failure ──► END
  │
  ▼
evaluate_sops  (Deterministic SOP Engine)
  │
  ├── no match ──► no_sop_fallback ──► END
  │
  ├── match ──► resolve_conflicts
  │                  │
  │                  ▼
  │            compose_response  (LLM: compose from facts)
  │                  │
  │                  ▼
  │                 END
```

### Key Components

| Component | Responsibility |
|-----------|---------------|
| **LangGraph** | Orchestrates the pipeline with conditional branching |
| **SOP Engine** | Deterministic policy evaluation (10 operators, all/any combinators) |
| **Weather Service** | Fetches live data from Open-Meteo |
| **Response Service** | LLM composes natural language from structured facts |
| **Session Repository** | Maintains conversation context within sessions |

---

## Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- An OpenAI API key (or compatible provider)

### Quick Start (Docker)

```bash
git clone <repo-url>
cd weather-advisory-bot

cp .env.example .env
# Edit .env and add your OPENAI_API_KEY

docker compose up --build
```

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API docs: http://localhost:8000/docs

### Local Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Local Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## Running Tests

```bash
cd backend
pytest tests/ -v
```

## Running Evaluations

```bash
cd backend
python -m evals.run_evals
```

Expected output:

```
========================================================
  Weather Advisory Bot Evaluation
========================================================

  [PASS] Direct SOP application
  [PASS] Paraphrased cycling intent
  [PASS] Child outdoor activity
  [PASS] Travel policy
  [PASS] Picnic fuzzy policy
  [PASS] Severe live weather
  [PASS] No SOP fallback
  [PASS] Weather API failure
  [PASS] Location failure
  [PASS] Prompt injection
  [PASS] Session memory
  [PASS] Multiple SOP conflict

  12/12 PASSED
========================================================
```

---

## Adding a New SOP

Edit `backend/app/policies/sops.yaml` and add a new entry:

```yaml
- id: SOP-013
  name: Moderate Rain Dog Walking
  category: pets
  severity: moderate

  applies_when:
    all:
      - field: activity_category
        operator: eq
        value: dog_walking
      - field: precipitation_probability
        operator: gte
        value: 70

  guidance:
    - Consider postponing the walk.
    - If going out, keep it short and carry rain gear.

  priority: 20
```

**No code changes required.** Restart the application and the new SOP is active.

---

## SOPs Included

| ID | Name | Category | Severity |
|----|------|----------|----------|
| SOP-001 | Extreme UV Outdoor Exercise | outdoor_exercise | high |
| SOP-002 | High Wind for Cycling | outdoor_exercise | high |
| SOP-003 | Heavy Rain Outdoor Activity | outdoor_activity | high |
| SOP-004 | High Rain Probability Travel | travel | moderate |
| SOP-005 | Strong Wind Travel | travel | moderate |
| SOP-006 | Children Extreme Heat | children | high |
| SOP-007 | Children High UV | children | moderate |
| SOP-008 | Elderly Extreme Heat | vulnerable_groups | high |
| SOP-009 | Pet Walking Extreme Heat | pets | high |
| SOP-010 | Thunderstorm Severe Weather | general_outdoor | critical |
| SOP-011 | Picnic Suitability (fuzzy) | general_outdoor | moderate |
| SOP-012 | Severe Weather Override | global | critical |

---

## Design Decisions

### Why LangGraph?
LangGraph provides a genuine graph with conditional branching. The pipeline has distinct failure paths (location failure, weather failure, no SOP match) that branch independently rather than running as a linear chain.

### Why deterministic SOP engine?
The LLM cannot be trusted to make safety decisions. The SOP engine evaluates conditions using pure logic (`gte`, `lte`, `in`, etc.) with `all`/`any` combinators, making decisions reproducible and auditable.

### Why Open-Meteo?
Open-Meteo provides free, reliable weather data with explicit field requests. No API key required for weather data.

### Why YAML for policies?
YAML is human-readable, easy to edit, and can be version-controlled. New SOPs can be added by non-developers without modifying Python code.

### Why LLM only for intent/composition?
The LLM excels at natural language understanding (mapping "ride my bike" → cycling) and composing friendly responses. It should not decide whether cycling is safe — that's the SOP engine's job.

### How are conflicts resolved?
When multiple SOPs match: `critical > high > moderate > low`. On tie, the `priority` field (higher wins) determines the winner. This is fully deterministic — the LLM never chooses.

### How is prompt injection handled?
User text is only used for intent extraction (activity, location, time). The SOP engine uses actual weather API values. The response composer receives pre-decided facts and cannot override the policy decision.

---

## API Reference

### POST /api/chat

```json
{
  "session_id": "uuid",
  "message": "Is it safe to cycle in Bhopal today?"
}
```

Response:

```json
{
  "session_id": "uuid",
  "answer": "...",
  "sop": { "id": "SOP-002", "name": "High Wind for Cycling", "severity": "high" },
  "weather": { "temperature_c": 31.2, "wind_speed_kmh": 44.1, ... },
  "location": { "name": "Bhopal", "latitude": 23.25, "longitude": 77.41 },
  "trace": [...]
}
```

### GET /api/session/{session_id}

Returns full session state for debugging.

### GET /api/health

Returns `{"status": "ok"}`.
