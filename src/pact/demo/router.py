"""FastAPI routes that drive the guided demo from the dashboard."""

from fastapi import APIRouter, HTTPException

from . import orchestrator

router = APIRouter(prefix="/demo", tags=["demo"])


@router.get("/scenarios")
def list_scenarios():
    """The 3 mini-demos available in the menu, in presentation order."""
    return orchestrator.scenarios()


@router.post("/reset")
def reset(scenario: str = "handshake"):
    """Wipe state, build the chosen mini-demo, return its outline."""
    return orchestrator.reset_session(scenario)


@router.post("/step")
async def step():
    """Run the next step (one Mercury 2 decision, or scripted fallback)."""
    if orchestrator.SESSION is None or not orchestrator.SESSION.started:
        raise HTTPException(409, "No demo session — call POST /demo/reset first")
    return await orchestrator.run_step()


@router.get("/state")
def get_state():
    return orchestrator.state()
