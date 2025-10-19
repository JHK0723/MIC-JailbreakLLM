from fastapi import FastAPI, Path, HTTPException
from fastapi.responses import StreamingResponse
from datetime import datetime
from typing import Dict, List
import logging
import asyncio
import os
from dotenv import load_dotenv
from models.level1 import run_level
from schema import SubmitRequest, ValidateRequest  #schema imports

load_dotenv()

app = FastAPI(title="Prompt Injection API")
logging.basicConfig(level=logging.INFO)

#track level completion status
team_levels: Dict[str, List[int]] = {}

LEVEL_PASSWORDS = {
    1: os.getenv("LEVEL1_PASSWORD"),
    2: os.getenv("LEVEL2_PASSWORD"),
    3: os.getenv("LEVEL3_PASSWORD"),
    4: os.getenv("LEVEL4_PASSWORD")
}

async def stream_response(response_text: str):
    """Stream model responses with typing effect"""
    words = response_text.split()
    for word in words:
        yield f"{word} "
        await asyncio.sleep(0.05 + (len(word) * 0.03))

@app.post("/submit/prompt")
async def submit_prompt(req: SubmitRequest):
    """Endpoint for submitting prompts to attempt jailbreak"""
    # Initialize new team
    if req.team_id not in team_levels:
        team_levels[req.team_id] = [0,0,0,0]
    
    # Check level access
    if req.level > 1 and not all(team_levels[req.team_id][:req.level-1]):
        raise HTTPException(status_code=403, detail="Complete previous levels first")

    # Get model response for the prompt
    result = run_level(req.level, req.text)
    
    # Stream response back with typing effect
    return StreamingResponse(
        stream_response(result.get("response", "")),
        media_type="text/event-stream"
    )

@app.post("/submit/validate")
async def validate_password(req: ValidateRequest):
    """Endpoint for validating discovered passwords"""
    if req.team_id not in team_levels:
        team_levels[req.team_id] = [0,0,0,0]
        
    if req.level > 1 and not all(team_levels[req.team_id][:req.level-1]):
        raise HTTPException(status_code=403, detail="Complete previous levels first")

    # Direct password comparison from env variables
    if req.password == LEVEL_PASSWORDS.get(req.level):
        team_levels[req.team_id][req.level-1] = 1
        next_level = req.level + 1 if req.level < 4 else None
        return {"valid": True, "next_level": next_level}
    
    return {"valid": False}

@app.get("/progress/{team_id}")
async def get_progress(team_id: str = Path(..., title="Team ID", min_length=1)):
    """Get team's level completion status"""
    if team_id not in team_levels:
        team_levels[team_id] = [0,0,0,0]
    return {
        "team_id": team_id,
        "levels": team_levels[team_id]
    }