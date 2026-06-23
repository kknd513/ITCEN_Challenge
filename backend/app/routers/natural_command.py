import os
from typing import Dict

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.command_mapper import map_question_to_command

router = APIRouter(prefix="/api/ops", tags=["natural-command"])

AGENT_URLS: Dict[str, str] = {
    "server-a": os.getenv("AGENT_A_URL", "http://localhost:9101"),
    "server-b": os.getenv("AGENT_B_URL", "http://localhost:9102"),
    "server-c": os.getenv("AGENT_C_URL", "http://localhost:9103"),
}

class NaturalCommandRequest(BaseModel):
    question: str
    dry_run: bool = False

class AgentCommandRequest(BaseModel):
    command: str
    intent: str

@router.post("/natural-command")
async def natural_command(req: NaturalCommandRequest):
    try:
        mapped = map_question_to_command(req.question)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if req.dry_run:
        return {"mapped": mapped, "executed": False, "output": None}

    agent_url = AGENT_URLS.get(mapped["server_id"])
    if not agent_url:
        raise HTTPException(status_code=404, detail=f"Agent URL not configured: {mapped['server_id']}")

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.post(f"{agent_url}/execute", json={"command": mapped["command"], "intent": mapped["intent"]})
            r.raise_for_status()
            result = r.json()
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Agent call failed: {e}")

    return {"mapped": mapped, "executed": True, "result": result}
