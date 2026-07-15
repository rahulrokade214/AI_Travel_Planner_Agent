# AI Travel Planner

An agentic AI trip-planning app: a LangGraph agent (FastAPI backend) that a
Streamlit chat UI talks to. The agent decides when to call tools (search,
places, etc.) before producing a final travel plan.

```
__start__ → agent ⇄ tools → __end__
```

---

## Project structure

```
AI_Travel_Planner/
├── agent/
│   └── agentic_workflow.py     # GraphBuilder — LangGraph agent + tools
├── main.py                     # FastAPI app, exposes POST /query
├── streamlit_app.py            # Chat UI, calls the FastAPI backend
├── setup.py
├── pyproject.toml
├── requirements.txt
├── uv.lock
├── .python-version
├── .gitignore
├── .dockerignore
├── Dockerfile.backend
├── Dockerfile.frontend
└── .env                        # NEVER commit this (API keys live here)
```

---

## 1. Local setup

```bash
# clone your repo, then:
python -m venv env
# Windows:
env\Scripts\activate.bat
# macOS/Linux:
source env/bin/activate

pip install -r requirements.txt
```

Create a `.env` file in the project root (this file is gitignored — never
commit it, and rotate any key that was ever pushed to GitHub even briefly):

```
MODEL_PROVIDER=groq
GROQ_API_KEY=your_key_here
# add any other keys agent/agentic_workflow.py needs (Tavily, OpenAI, Google Places, etc.)
```

Run both services locally, in two terminals:

```bash
uvicorn main:app --reload --port 8000
```
```bash
streamlit run streamlit_app.py
```

The UI defaults to `BASE_URL=http://localhost:8000` when no `BASE_URL` env
var is set, so local dev works with zero config.

---

## 2. Before deploying — fix these first

These were found in the uploaded project and will cause build failures or
confusion if left as-is:

- **`pyproject.toml`** had a typo dependency (`panda>=0.3.1`) and a
  non-existent `pandas>=3.0.3` version, plus was missing the `[project]`
  table entirely. Replaced with a valid, minimal `pyproject.toml` (included
  here) — `setup.py` + `requirements.txt` remain the source of truth for
  installs; this file just makes `pip install -e .` valid.
- **`.python-version`** said `3.12` while the README's `uv` setup used
  `3.10`. Both Dockerfiles here pin `python:3.12-slim` to match
  `.python-version` — if you actually developed against 3.10, either update
  `.python-version` to `3.10` or change the Dockerfiles' base image tag to
  match. Pick one and keep them consistent.
- **`streamlit_app.py`** now reads `BASE_URL` from an environment variable
  instead of hardcoding `localhost` (see the version included here).

---

## 3. Deploying to Google Cloud (Cloud Run)

Google Cloud doesn't have a dedicated "Streamlit hosting" product, so the
standard pattern is: **two separate Cloud Run services** — one for the
FastAPI backend, one for the Streamlit frontend — each in its own
container, talking to each other over HTTPS.

### Prerequisites
```bash
# Install gcloud CLI, then:
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
gcloud services enable run.googleapis.com artifactregistry.googleapis.com secretmanager.googleapis.com
```

### Step 1 — Store your API keys in Secret Manager (not in the image)
```bash
echo -n "your_groq_key" | gcloud secrets create GROQ_API_KEY --data-file=-
# repeat for any other keys (TAVILY_API_KEY, OPENAI_API_KEY, etc.)
```

### Step 2 — Deploy the backend
From the project root (where `Dockerfile.backend`, `main.py`, `agent/`,
`requirements.txt`, `setup.py` all live):

```bash
gcloud run deploy travel-planner-backend \
  --source . \
  --dockerfile Dockerfile.backend \
  --region asia-south1 \
  --allow-unauthenticated \
  --set-secrets=GROQ_API_KEY=GROQ_API_KEY:latest \
  --set-env-vars=MODEL_PROVIDER=groq
```

This builds the image with Cloud Build and deploys it. Note the URL it
prints, e.g. `https://travel-planner-backend-xxxxx-el.a.run.app`.

### Step 3 — Deploy the frontend, pointing at the backend URL
```bash
gcloud run deploy travel-planner-frontend \
  --source . \
  --dockerfile Dockerfile.frontend \
  --region asia-south1 \
  --allow-unauthenticated \
  --set-env-vars=BASE_URL=https://travel-planner-backend-xxxxx-el.a.run.app
```

Note the frontend URL it prints — that's your live app.

### Step 4 (recommended) — lock down CORS
Right now `main.py` has `allow_origins=["*"]`. Once you have the frontend's
real Cloud Run URL, tighten this in `main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://travel-planner-frontend-xxxxx-el.a.run.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```
Redeploy the backend after this change.

### Notes on cost/behavior
- Cloud Run scales to zero when idle — no traffic, no charge — but the
  first request after idle ("cold start") takes a few seconds while the
  container spins up, longer if LangGraph/LangChain imports are heavy.
- `region` above uses `asia-south1` (Mumbai) since your other context is
  India-based — change it if you want a different region.
- If `agent/agentic_workflow.py` calls out to Tavily, Google Places, or
  OpenAI, remember to add each of those as its own secret and
  `--set-secrets` entry in Step 2.

---

## 4. Redeploying after code changes
Cloud Run + `--source .` rebuilds from your local directory each time, so
updating is just re-running the same `gcloud run deploy` command for
whichever service changed.

---

## Security checklist
- [ ] `.env` is in `.gitignore` and was never committed
- [ ] If any key was ever pushed to GitHub (even briefly), rotate it —
      removing it later doesn't erase it from git history
- [ ] Secrets are in Secret Manager, not baked into the Docker image or
      passed as plain `--set-env-vars`
- [ ] CORS `allow_origins` is locked to your actual frontend URL, not `*`,
      once you're past initial testing