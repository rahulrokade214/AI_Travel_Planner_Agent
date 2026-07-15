from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from agent.agentic_workflow import GraphBuilder
from starlette.responses import JSONResponse
import os
import datetime
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv(override=True)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # set specific origins in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Read once at startup so you can SEE in the terminal logs which provider is active.
MODEL_PROVIDER = os.getenv("MODEL_PROVIDER", "groq").strip().lower()
if MODEL_PROVIDER not in {"openai", "groq"}:
    print(f"[WARNING] Unknown MODEL_PROVIDER='{MODEL_PROVIDER}' in .env — falling back to 'groq'")
    MODEL_PROVIDER = "groq"

print(f"[STARTUP] Travel Planner is using MODEL_PROVIDER = '{MODEL_PROVIDER}'")


@app.get("/")
async def root():
    return {
        "status": "ok",
        "message": "Travel Planner API is running. Use POST /query to send requests.",
        "model_provider": MODEL_PROVIDER,
    }


class QueryRequest(BaseModel):
    question: str


@app.post("/query")
async def query_travel_agent(query: QueryRequest):
    try:
        print(f"[QUERY] provider={MODEL_PROVIDER} question={query.question!r}")

        graph = GraphBuilder(model_provider=MODEL_PROVIDER)
        react_app = graph()

        try:
            png_graph = react_app.get_graph().draw_mermaid_png()
            with open("my_graph.png", "wb") as f:
                f.write(png_graph)
            print(f"Graph saved as 'my_graph.png' in {os.getcwd()}")
        except Exception as graph_err:
            # Don't let graph-image rendering (needs internet/mermaid service)
            # take down the whole request if it fails.
            print(f"[WARNING] Could not render graph image: {graph_err}")

        messages = {"messages": [query.question]}
        output = react_app.invoke(messages)

        if isinstance(output, dict) and "messages" in output:
            final_output = output["messages"][-1].content  # Last AI response
        else:
            final_output = str(output)

        return {"answer": final_output, "model_provider": MODEL_PROVIDER}

    except Exception as e:
        # Surface which provider was active when the error happened —
        # makes it obvious in the frontend if the wrong provider was used.
        print(f"[ERROR] provider={MODEL_PROVIDER} error={e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "model_provider": MODEL_PROVIDER},
        )