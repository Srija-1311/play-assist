# PlayAssist: Agentic Game Support & Match Insights Assistant

PlayAssist is a full-stack AI assistant that answers game-support and player-stats questions by **choosing and calling tools** instead of guessing. A React + TypeScript chat UI sits on a FastAPI backend that runs a LangChain tool-calling agent, and every tool call is shown in the UI so you can see how each answer was produced.

> **Demo:** _add your deployed link here_  
> **Player stats question with tool calls** (docs/chat-stats.png)
> **Support question grounded in the knowledge base** (docs/chat-support.png)
> **Unknown player** (docs/chat-notfound.png)

## Features

- **Tool-calling agent loop:** the LLM decides which tool to call, the backend runs it, and the result is fed back until the model produces a final answer (capped at 5 steps).
- **Three tools**
  - `get_player_stats`: looks up a player's matches, wins, kills, deaths and hours from SQLite.
  - `search_kb`: keyword search over a small support knowledge base (passwords, refunds, lag, matchmaking).
  - `calculate`: a safe arithmetic evaluator for win rate, K/D ratio and percentages (AST-based, no `eval`).
- **Transparent UI:** a collapsible panel lists each tool call with its arguments and result.
- **Grounded answers:** the system prompt tells the model to answer only the latest message and to base support answers strictly on the retrieved article.
- **Provider-agnostic:** works with any OpenAI-compatible endpoint (Groq, OpenAI, Ollama) by changing three environment variables.
- **Evaluation suite:** 12 test cases check tool selection, answer correctness, and hallucinated details.

## Architecture

```
React + TypeScript UI
        |  POST /chat  { messages }
        v
FastAPI  --validates input (Pydantic), CORS-->  Agent loop (LangChain)
                                                  |  LLM picks a tool
                                                  v
                                   get_player_stats | search_kb | calculate
                                                  |  result returned to the LLM
                                                  v
                          final answer + tool-call trace  -->  UI
```

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | React, TypeScript, Vite |
| Backend | Python, FastAPI, Pydantic |
| AI | LangChain (`langchain-openai`), Groq API (OpenAI-compatible) |
| Data | SQLite |
| Deployment | Docker, Render (backend), Vercel (frontend) |

## Project structure

```
playassist/
├── backend/
│   ├── main.py            # FastAPI app: /health, /chat
│   ├── agent.py           # tool-calling loop and system prompt
│   ├── tools.py           # the three tools, sample data and knowledge base
│   ├── eval.py            # evaluation suite
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
└── frontend/
    └── src/App.tsx        # chat UI with tool-call panel
```

## Getting started

### 1. Backend

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate    macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env     # then edit .env
uvicorn main:app --reload
```

Open http://localhost:8000/docs to try the `/chat` endpoint.

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173. To point the UI at a deployed backend, set `VITE_API_URL` (no trailing slash).

### Environment variables (`backend/.env`)

| Variable | Description | Example |
|---|---|---|
| `OPENAI_API_KEY` | API key for your provider | `gsk_...` |
| `OPENAI_BASE_URL` | OpenAI-compatible endpoint | `https://api.groq.com/openai/v1` |
| `MODEL` | Model ID that supports tool calling | check your provider's model list |
| `CORS_ORIGINS` | Comma-separated allowed frontend origins | `http://localhost:5173` |

Never commit `.env`. It is listed in `.gitignore`.

## API

`POST /chat`

```json
{ "messages": [ { "role": "user", "content": "What is Maya's win rate?" } ] }
```

Response:

```json
{
  "answer": "Maya has won about 61.2% of her matches (251 of 410).",
  "trace": [
    { "tool": "get_player_stats", "args": { "name": "Maya" }, "result": "{...}" },
    { "tool": "calculate", "args": { "expression": "251/410*100" }, "result": "61.21..." }
  ]
}
```

`GET /health` returns `{"status": "ok"}`. Errors from the LLM provider return HTTP 502.

## Evaluation

```bash
cd backend
python eval.py
```

The suite has 12 cases:

- **Stats and math (6):** win rate, K/D ratio, a comparison between players, and a percentage calculation. Checks that the right tools are used and the numbers are correct.
- **Unknown player (1):** checks that the agent says the player was not found instead of inventing stats.
- **Knowledge base (4):** password reset, refund eligibility, ranked placement, lag troubleshooting. Checks tool use and correct facts.
- **Hallucination check (1):** the refund-process question must contain the policy facts and must **not** contain details absent from the knowledge base (portals, order IDs, timelines).

**Results:** 11-12 of 12 cases passed across 3 runs with Groq. Scores vary slightly between runs because hosted models are not fully deterministic.

**What testing found:** early on, the agent repeated an earlier answer and invented refund steps that were not in the knowledge base. Tightening the system prompt (answer only the latest message, stay strictly within retrieved articles) fixed both, and the hallucination check was added to catch regressions.

## Design notes

- **Safe calculator:** arithmetic is parsed with Python's `ast` module and limited to basic operators, so no model-supplied code is executed.
- **Bounded agent loop:** at most 5 tool-calling steps, with tool errors returned to the model as text instead of crashing the request.
- **Input validation:** Pydantic limits message count (20) and message length (2,000 characters).
- **Parameterized SQL:** player lookups use query parameters.

## Limitations

- The data is sample data (3 players, 4 support articles). It is a demo, not a production system.
- `search_kb` uses keyword overlap, not semantic search.
- No streaming; the full answer arrives at once.
- No authentication or rate limiting on the API.
- The evaluation suite is small and checks answers with regular expressions.

## Deployment

**Backend (Render):** create a Web Service from the repo with Root Directory `backend` and Runtime Docker, then set `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `MODEL` and `CORS_ORIGINS` as environment variables. Verify with `/health`.

**Frontend (Vercel):** import the repo, set the Root Directory to `frontend`, and add `VITE_API_URL` pointing at the Render URL. Then add the Vercel URL to `CORS_ORIGINS` on Render and redeploy.

Free tiers may sleep when idle, so the first request can be slow.

## Roadmap

- Stream responses to the UI
- Replace keyword search with embeddings and a vector store
- Add pytest unit tests and a GitHub Actions workflow
- Add conversation memory and per-user rate limiting
