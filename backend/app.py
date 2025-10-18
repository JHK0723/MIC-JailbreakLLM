from fastapi import FastAPI, Path
from datetime import datetime
from typing import List, Dict, Any
import logging

from models.level1 import run_level
from .schema import AttackRequest, SubmitRequest

app = FastAPI(title="Prompt Injection API")

logging.basicConfig(level=logging.INFO)

team_submissions: Dict[str, List[Dict[str, Any]]] = {}

@app.post("/attack")
def attack(req: AttackRequest):
    secret_word = "apple"

    if secret_word.lower() in req.prompt.lower():
        reply = f"🤖 Congrats! You discovered the password: *{secret_word}*"
        success = True
    else:
        reply = "🤖 Access denied. Try rephrasing your prompt cleverly."
        success = False

    return {
        "team_id": req.team_id,
        "prompt": req.prompt,
        "response": reply,
        "success": success,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/submit")
def submit(req: SubmitRequest):
    level_data = {
        "system_prompt": "Your system prompt here",
        "hints": "Hints can go here",
        "secret": "sunrise42"
    }

    result = run_level(level_data, req.text)

    if result.get("success"):
        logging.info(f"Team {req.team_id} submission SUCCESSFUL: {req.text}")
    else:
        logging.info(f"Team {req.team_id} submission UNSUCCESSFUL: {req.text}")

    team_submissions.setdefault(req.team_id, []).append({
        "prompt": req.text,
        "result": result,
        "timestamp": datetime.now().isoformat()
    })

    return {"status": "successful" if result.get("success") else "unsuccessful"}

@app.get("/team/{team_id}")
def get_team_submissions(team_id: str = Path(..., title="Team ID", min_length=1)):
    return {"team_id": team_id, "submissions": team_submissions.get(team_id, [])}
