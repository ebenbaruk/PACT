"""PACT server — all endpoints, in-memory storage."""

import uuid
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .crypto import verify
from .templates import TEMPLATES, validate_message

app = FastAPI(title="PACT — Protocol for Agent Coordination & Trust", version="0.1.0")

# ── In-memory storage ──────────────────────────────────────────────────────────
agents: dict[str, dict] = {}
bonds: dict[str, dict] = {}
interactions: dict[str, dict] = {}
intents: dict[str, dict] = {}


# ── Request models ─────────────────────────────────────────────────────────────
class RegisterAgent(BaseModel):
    domain: str
    name: str
    public_key: str
    capabilities: list[str] = []


class ProposeBond(BaseModel):
    proposer_id: str
    accepter_id: str
    terms: dict
    signature: str


class AcceptBond(BaseModel):
    signature: str


class BroadcastIntent(BaseModel):
    agent_id: str
    need: str
    requirements: list[str] = []


class RespondIntent(BaseModel):
    agent_id: str
    message: str


class NetworkQuery(BaseModel):
    agent_id: str
    need: str


class CreateInteraction(BaseModel):
    bond_id: str
    template: str
    initiator_id: str


class SendMessage(BaseModel):
    sender_id: str
    data: dict
    signature: str


# ── Helpers ────────────────────────────────────────────────────────────────────
def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _agent_or_404(agent_id: str) -> dict:
    if agent_id not in agents:
        raise HTTPException(404, f"Agent {agent_id} not found")
    return agents[agent_id]


def _bond_or_404(bond_id: str) -> dict:
    if bond_id not in bonds:
        raise HTTPException(404, f"Bond {bond_id} not found")
    return bonds[bond_id]


def _get_agent_bonds(agent_id: str) -> list[dict]:
    return [
        b for b in bonds.values()
        if b["status"] == "active" and (b["proposer_id"] == agent_id or b["accepter_id"] == agent_id)
    ]


def _trust_score(agent_id: str) -> float:
    agent_bonds = _get_agent_bonds(agent_id)
    bond_count = len(agent_bonds)
    referral_count = sum(
        1 for i in intents.values()
        for r in i.get("responses", [])
        if r.get("referral_from") and (r.get("agent_id") == agent_id or r.get("referral_from") == agent_id)
    )
    if agent_bonds:
        avg_age = sum(
            (datetime.now(timezone.utc) - datetime.fromisoformat(b["created_at"])).days
            for b in agent_bonds
        ) / len(agent_bonds)
    else:
        avg_age = 0
    return min(1.0, bond_count * 0.15 + referral_count * 0.1 + avg_age / 365 * 0.3)


# ── Phase 1: Handshake ────────────────────────────────────────────────────────
@app.post("/agents/register")
def register_agent(req: RegisterAgent):
    agent_id = str(uuid.uuid4())[:8]
    agents[agent_id] = {
        "id": agent_id,
        "domain": req.domain,
        "name": req.name,
        "public_key": req.public_key,
        "capabilities": req.capabilities,
        "verified": False,
        "created_at": _now(),
    }
    return agents[agent_id]


@app.post("/agents/{agent_id}/verify")
def verify_agent(agent_id: str):
    agent = _agent_or_404(agent_id)
    agent["verified"] = True
    return {"status": "verified", "agent_id": agent_id}


@app.get("/agents/{agent_id}")
def get_agent(agent_id: str):
    return _agent_or_404(agent_id)


@app.get("/agents/{agent_id}/trust")
def get_trust(agent_id: str):
    _agent_or_404(agent_id)
    return {"agent_id": agent_id, "trust_score": round(_trust_score(agent_id), 3)}


@app.post("/bonds/propose")
def propose_bond(req: ProposeBond):
    proposer = _agent_or_404(req.proposer_id)
    _agent_or_404(req.accepter_id)
    terms_str = str(sorted(req.terms.items()))
    if not verify(terms_str, req.signature, proposer["public_key"]):
        raise HTTPException(400, "Invalid signature on bond proposal")
    bond_id = str(uuid.uuid4())[:8]
    bonds[bond_id] = {
        "id": bond_id,
        "proposer_id": req.proposer_id,
        "accepter_id": req.accepter_id,
        "terms": req.terms,
        "status": "proposed",
        "signatures": {"proposer": req.signature},
        "created_at": _now(),
    }
    return bonds[bond_id]


@app.post("/bonds/{bond_id}/accept")
def accept_bond(bond_id: str, req: AcceptBond):
    bond = _bond_or_404(bond_id)
    if bond["status"] != "proposed":
        raise HTTPException(400, "Bond is not in proposed state")
    accepter = agents[bond["accepter_id"]]
    terms_str = str(sorted(bond["terms"].items()))
    if not verify(terms_str, req.signature, accepter["public_key"]):
        raise HTTPException(400, "Invalid signature on bond acceptance")
    bond["status"] = "active"
    bond["signatures"]["accepter"] = req.signature
    bond["accepted_at"] = _now()
    return bond


@app.get("/bonds")
def list_bonds():
    return list(bonds.values())


@app.get("/bonds/{bond_id}")
def get_bond(bond_id: str):
    return _bond_or_404(bond_id)


# ── Phase 2: Discovery ────────────────────────────────────────────────────────
@app.post("/intents/broadcast")
def broadcast_intent(req: BroadcastIntent):
    _agent_or_404(req.agent_id)
    intent_id = str(uuid.uuid4())[:8]
    intents[intent_id] = {
        "id": intent_id,
        "agent_id": req.agent_id,
        "need": req.need,
        "requirements": req.requirements,
        "status": "open",
        "responses": [],
        "created_at": _now(),
    }
    return intents[intent_id]


@app.get("/intents/matching/{agent_id}")
def get_matching_intents(agent_id: str):
    agent = _agent_or_404(agent_id)
    caps = set(c.lower() for c in agent.get("capabilities", []))
    matches = []
    for intent in intents.values():
        if intent["status"] != "open" or intent["agent_id"] == agent_id:
            continue
        reqs = set(r.lower() for r in intent.get("requirements", []))
        if reqs & caps:
            matches.append(intent)
    return matches


@app.post("/intents/{intent_id}/respond")
def respond_to_intent(intent_id: str, req: RespondIntent):
    if intent_id not in intents:
        raise HTTPException(404, f"Intent {intent_id} not found")
    _agent_or_404(req.agent_id)
    intent = intents[intent_id]
    response = {"agent_id": req.agent_id, "message": req.message, "created_at": _now()}
    intent["responses"].append(response)
    return response


# ── Phase 3: Web of Trust ─────────────────────────────────────────────────────
@app.post("/network/query")
def query_network(req: NetworkQuery):
    _agent_or_404(req.agent_id)
    my_bonds = _get_agent_bonds(req.agent_id)
    partner_ids = set()
    for b in my_bonds:
        other = b["accepter_id"] if b["proposer_id"] == req.agent_id else b["proposer_id"]
        partner_ids.add(other)

    recommendations = []
    for pid in partner_ids:
        partner = agents[pid]
        partner_bonds = _get_agent_bonds(pid)
        for pb in partner_bonds:
            candidate_id = pb["accepter_id"] if pb["proposer_id"] == pid else pb["proposer_id"]
            if candidate_id == req.agent_id or candidate_id in partner_ids:
                continue
            candidate = agents[candidate_id]
            caps = set(c.lower() for c in candidate.get("capabilities", []))
            if req.need.lower() in caps or any(req.need.lower() in c for c in caps):
                recommendations.append({
                    "agent_id": candidate_id,
                    "agent_name": candidate["name"],
                    "referred_by": pid,
                    "referred_by_name": partner["name"],
                    "capabilities": candidate["capabilities"],
                    "trust_score": round(_trust_score(candidate_id), 3),
                })
    return recommendations


@app.get("/agents/{agent_id}/network")
def get_network(agent_id: str):
    _agent_or_404(agent_id)
    my_bonds = _get_agent_bonds(agent_id)
    partners = []
    for b in my_bonds:
        other_id = b["accepter_id"] if b["proposer_id"] == agent_id else b["proposer_id"]
        other = agents[other_id]
        partners.append({
            "agent_id": other_id,
            "name": other["name"],
            "bond_id": b["id"],
            "trust_score": round(_trust_score(other_id), 3),
        })
    return partners


# ── Interactions ───────────────────────────────────────────────────────────────
@app.post("/interactions/create")
def create_interaction(req: CreateInteraction):
    _bond_or_404(req.bond_id)
    if req.template not in TEMPLATES:
        raise HTTPException(400, f"Unknown template: {req.template}")
    interaction_id = str(uuid.uuid4())[:8]
    interactions[interaction_id] = {
        "id": interaction_id,
        "bond_id": req.bond_id,
        "template": req.template,
        "initiator_id": req.initiator_id,
        "messages": [],
        "current_step": 0,
        "status": "active",
        "created_at": _now(),
    }
    return interactions[interaction_id]


@app.post("/interactions/{interaction_id}/message")
def send_message(interaction_id: str, req: SendMessage):
    if interaction_id not in interactions:
        raise HTTPException(404, f"Interaction {interaction_id} not found")
    ix = interactions[interaction_id]
    if ix["status"] != "active":
        raise HTTPException(400, "Interaction is not active")

    sender = _agent_or_404(req.sender_id)
    data_str = str(sorted(req.data.items()))
    if not verify(data_str, req.signature, sender["public_key"]):
        raise HTTPException(400, "Invalid message signature")

    error = validate_message(ix["template"], ix["current_step"], req.data)
    if error:
        raise HTTPException(400, error)

    msg = {"sender_id": req.sender_id, "data": req.data, "step": ix["current_step"], "created_at": _now()}
    ix["messages"].append(msg)
    ix["current_step"] += 1

    template = TEMPLATES[ix["template"]]
    if ix["current_step"] >= len(template["steps"]):
        ix["status"] = "completed"

    return {"message": msg, "interaction_status": ix["status"]}
