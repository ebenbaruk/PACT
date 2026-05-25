"""Server-side orchestrator for the guided PACT demo.

Three short, independent mini-demos — one per protocol mechanism, each ~3 clicks
with the minimal cast of *business* agents needed to make the point:

- handshake  : Acheteur ↔ Fournisseur — seal a signed, unforgeable agreement.
- discovery  : Acheteur finds an unknown Logistique by broadcasting a need.
- weboftrust : Acheteur reaches a Comptable through a trusted referral.

``reset_session(scenario)`` builds the right agents + steps; ``run_step`` runs the
next step (one Mercury 2 decision, or a deterministic fallback) and returns a
structured trace for the dashboard. ``run_step`` is awaited from an async endpoint
via ``run_in_threadpool`` under a lock so the blocking agent work can't deadlock
the event loop (see ``router.py``).
"""

import asyncio
from dataclasses import dataclass, field
from typing import Callable

from starlette.concurrency import run_in_threadpool

from ..ai.agent import PACTAgent

# ── Business agents (role-based, kept deliberately simple) ──────────────────────
_PERSONAS = {
    "acheteur": dict(
        name="Agent Acheteur", domain="acheteur.bizagent.ai",
        persona="Tu es l'agent IA d'une entreprise acheteuse. Tu cherches des partenaires fiables "
                "(fournisseurs, transporteurs, comptables) et tu formalises des accords clairs et signés. "
                "Tes termes restent simples.",
        capabilities=["procurement", "purchasing"],
    ),
    "fournisseur": dict(
        name="Agent Fournisseur", domain="fournisseur.bizagent.ai",
        persona="Tu es l'agent IA d'un fournisseur de pièces industrielles. Tu réponds aux propositions "
                "d'accord et tu travailles avec des partenaires de confiance.",
        capabilities=["supply", "parts", "manufacturing"],
    ),
    "logistique": dict(
        name="Agent Logistique", domain="logistique.bizagent.ai",
        persona="Tu es l'agent IA d'une entreprise de transport et logistique. Nouveau sur le réseau, "
                "tu cherches des clients et tu réponds aux besoins de livraison.",
        capabilities=["logistics", "delivery", "transport"],
    ),
    "comptable": dict(
        name="Agent Comptable", domain="comptable.bizagent.ai",
        persona="Tu es l'agent IA d'un service de comptabilité et facturation. Tu fournis des factures "
                "et tu travailles via recommandation de partenaires de confiance.",
        capabilities=["accounting", "invoicing", "billing"],
    ),
}

SCENARIOS_META = {
    "handshake": {
        "id": "handshake", "num": 1, "title": "Handshake",
        "tagline": "Sceller un accord infalsifiable",
        "problem": "Un agent Acheteur et un agent Fournisseur, qui ne se connaissent pas, veulent faire "
                   "affaire. Comment sceller un accord que ni l'un ni l'autre ne peut falsifier ni renier ?",
        "punchline": "Deux entreprises qui ne se connaissaient pas ont un contrat numérique vérifiable — "
                     "chaque signature est opposable, sans tiers de confiance.",
    },
    "discovery": {
        "id": "discovery", "num": 2, "title": "Discovery",
        "tagline": "Se trouver sans annuaire",
        "problem": "L'agent Acheteur a besoin d'un transporteur mais n'en connaît aucun, et il n'existe "
                   "aucun annuaire central. Comment trouver le bon partenaire ?",
        "punchline": "Deux agents se sont trouvés tout seuls, par capacité déclarée — sans annuaire ni "
                     "intermédiaire humain.",
    },
    "weboftrust": {
        "id": "weboftrust", "num": 3, "title": "Web of Trust",
        "tagline": "La confiance se propage",
        "problem": "L'agent Acheteur a besoin d'un service de facturation mais ne veut pas traiter avec un "
                   "inconnu. Il s'appuie sur ceux en qui il a déjà confiance.",
        "punchline": "La confiance se propage de proche en proche — une recommandation entre partenaires "
                     "suffit à créer un nouveau lien fiable.",
    },
}
SCENARIO_AGENTS = {
    "handshake": ["acheteur", "fournisseur"],
    "discovery": ["acheteur", "logistique"],
    "weboftrust": ["acheteur", "fournisseur", "comptable"],
}
SCENARIO_ORDER = ["handshake", "discovery", "weboftrust"]


# ── Session state ───────────────────────────────────────────────────────────────
@dataclass
class Session:
    scenario_id: str
    agents: dict[str, PACTAgent]
    steps: list["Step"]
    step_idx: int = 0
    started: bool = False
    history: list[dict] = field(default_factory=list)

    def id_to_name(self) -> dict[str, str]:
        return {a.agent_id: a.name for a in self.agents.values() if a.agent_id}

    def agent_display(self, key: str) -> dict:
        if key == "system":
            return {"key": "system", "name": "Réseau PACT", "icon": "🌐"}
        a = self.agents[key]
        return {"key": key, "name": a.name, "icon": a.icon}


@dataclass
class Step:
    id: int
    phase: str
    narration_fr: str
    agent_key: str                                    # primary actor (or "system")
    scripted: Callable[[Session], dict]               # deterministic path (used as fallback)
    ai_instruction: Callable[[Session], str] | None = None  # None = always scripted
    peer_key: str | None = None                       # counterparty, for message "to" resolution
    post: Callable[[Session], dict] | None = None     # deterministic follow-through after the main action


SESSION: Session | None = None
_lock = asyncio.Lock()


# ── Reusable scripted helpers ───────────────────────────────────────────────────
def _join(s: Session, keys: list[str]) -> list[dict]:
    """Register + verify a set of agents; return trace events."""
    events: list[dict] = []
    for k in keys:
        a = s.agents[k]
        _, ev, _ = a.run_tool_traced("register_agent", {})
        events += ev
        if a.agent_id:
            _, ev2, _ = a.run_tool_traced("verify_agent", {"agent_id": a.agent_id})
            events += ev2
        events.append({"kind": "thinking",
                       "text": f"{a.icon} {a.name} rejoint le réseau — capacités : {', '.join(a.capabilities)}."})
    return events


def _make_bond(s: Session, proposer_key: str, accepter_key: str, terms: dict):
    p, a = s.agents[proposer_key], s.agents[accepter_key]
    res, ev, m = p.run_tool_traced("propose_bond", {"accepter_id": a.agent_id, "terms": terms},
                                   peers=s.id_to_name(), default_to=a.name)
    bond_id = res.get("id") if isinstance(res, dict) else None
    if bond_id:
        _, ev2, m2 = a.run_tool_traced("accept_bond", {"bond_id": bond_id},
                                       peers=s.id_to_name(), default_to=p.name)
        ev += ev2
        m += m2
    return ev, m


def _accept_pending(s: Session, accepter_key: str, proposer_key: str) -> dict:
    """List bonds, find the bond proposer→accepter still 'proposed', accept it."""
    acc, prop = s.agents[accepter_key], s.agents[proposer_key]
    res, events, _ = acc.run_tool_traced("list_bonds", {})
    bond_id = None
    if isinstance(res, list):
        for b in res:
            if (b.get("status") == "proposed" and b.get("accepter_id") == acc.agent_id
                    and b.get("proposer_id") == prop.agent_id):
                bond_id = b["id"]
                break
    messages = []
    if bond_id:
        _, ev2, m2 = acc.run_tool_traced("accept_bond", {"bond_id": bond_id},
                                         peers=s.id_to_name(), default_to=prop.name)
        events += ev2
        messages += m2
    return {"events": events, "messages": messages,
            "final_text": f"J'ai vérifié la proposition de {prop.name} et signé l'accord."}


def _post_accept(s: Session, accepter_key: str, proposer_key: str) -> dict:
    r = _accept_pending(s, accepter_key, proposer_key)
    return {"events": r["events"], "messages": r["messages"]}


def _post_discovery_bond(s: Session) -> dict:
    """After Logistique responds, the two form an active partnership."""
    log, ach = s.agents["logistique"], s.agents["acheteur"]
    terms = {"service": "transport", "sla": "48h", "insurance": "included"}
    res, ev, m = log.run_tool_traced("propose_bond", {"accepter_id": ach.agent_id, "terms": terms},
                                     peers=s.id_to_name(), default_to=ach.name)
    bond_id = res.get("id") if isinstance(res, dict) else None
    if bond_id:
        _, ev2, m2 = ach.run_tool_traced("accept_bond", {"bond_id": bond_id},
                                         peers=s.id_to_name(), default_to=log.name)
        ev += ev2
        m += m2
    return {"events": ev, "messages": m}


# ── Scenario builders ───────────────────────────────────────────────────────────
def build_handshake() -> list["Step"]:
    def s1(s):
        ev = _join(s, ["acheteur", "fournisseur"])
        return {"agent_display": s.agent_display("system"), "events": ev, "messages": [],
                "final_text": "Deux agents d'entreprises distinctes ont publié leur identité signée (Ed25519)."}

    def s2(s):
        ach, fou = s.agents["acheteur"], s.agents["fournisseur"]
        _, ev, m = ach.run_tool_traced(
            "propose_bond", {"accepter_id": fou.agent_id,
                             "terms": {"service": "supply-contract", "price": "12000 EUR", "delivery": "30 jours"}},
            peers=s.id_to_name(), default_to=fou.name)
        return {"events": ev, "messages": m, "final_text": "J'ai proposé un accord signé au Fournisseur."}

    return [
        Step(1, "Handshake",
             "Les deux agents rejoignent le réseau et publient leur identité cryptographique (clé Ed25519).",
             "system", s1),
        Step(2, "Handshake",
             "L'Acheteur propose un accord signé au Fournisseur : service, prix, délai. La signature engage son identité.",
             "acheteur", s2,
             ai_instruction=lambda s: (
                 f"Propose un bond à Agent Fournisseur (agent_id={s.agents['fournisseur'].agent_id}) avec terms : "
                 f"service='supply-contract', price='12000 EUR', delivery='30 jours'."),
             peer_key="fournisseur"),
        Step(3, "Handshake",
             "Le Fournisseur vérifie la signature et contre-signe. L'accord devient actif — infalsifiable et opposable aux deux parties.",
             "fournisseur", lambda s: _accept_pending(s, "fournisseur", "acheteur"),
             ai_instruction=lambda s: (
                 f"Agent Acheteur (agent_id={s.agents['acheteur'].agent_id}) a proposé un bond. "
                 f"List bonds, trouve le bond en attente avec l'Acheteur, accepte-le."),
             peer_key="acheteur"),
    ]


def build_discovery() -> list["Step"]:
    def s1(s):
        ev = _join(s, ["acheteur", "logistique"])
        return {"agent_display": s.agent_display("system"), "events": ev, "messages": [],
                "final_text": "Deux agents sur le réseau — aucun lien entre eux, ils ne se connaissent pas."}

    def s2(s):
        ach = s.agents["acheteur"]
        _, ev, m = ach.run_tool_traced(
            "broadcast_intent",
            {"need": "transport de marchandises", "requirements": ["logistics", "delivery"]},
            peers=s.id_to_name())
        return {"events": ev, "messages": m, "final_text": "J'ai diffusé mon besoin de transport à tout le réseau."}

    def s3(s):
        log, ach = s.agents["logistique"], s.agents["acheteur"]
        res, ev, m = log.run_tool_traced("check_matching_intents", {})
        intent_id = res[0]["id"] if isinstance(res, list) and res else None
        messages = m[:]
        if intent_id:
            _, ev2, m2 = log.run_tool_traced(
                "respond_to_intent",
                {"intent_id": intent_id, "message": "Transport et livraison sous 48h, assurance incluse."},
                peers=s.id_to_name(), default_to=ach.name)
            ev += ev2
            messages += m2
        return {"events": ev, "messages": messages,
                "final_text": "J'ai repéré le besoin de l'Acheteur et j'ai répondu avec mon offre."}

    return [
        Step(1, "Discovery",
             "Deux agents rejoignent le réseau. Ils ne se connaissent pas — aucun lien entre eux.",
             "system", s1),
        Step(2, "Discovery",
             "L'Acheteur a besoin d'un transporteur mais n'en connaît aucun, et il n'y a pas d'annuaire central. Il diffuse son besoin sur le réseau.",
             "acheteur", s2,
             ai_instruction=lambda s: (
                 "Tu cherches un transporteur / logisticien. Diffuse un intent avec "
                 "need='transport de marchandises' et requirements : 'logistics' et 'delivery'.")),
        Step(3, "Discovery",
             "Un agent Logistique, jamais sollicité, voit que ses capacités correspondent et répond. Les deux nouent aussitôt un partenariat.",
             "logistique", s3,
             ai_instruction=lambda s: (
                 "Vérifie les intents ouverts qui correspondent à tes capacités. Si tu en trouves un, "
                 "réponds avec un message décrivant ton offre de transport."),
             peer_key="acheteur", post=_post_discovery_bond),
    ]


def build_weboftrust() -> list["Step"]:
    def s1(s):
        ev = _join(s, ["acheteur", "fournisseur", "comptable"])
        messages: list[dict] = []
        e1, m1 = _make_bond(s, "acheteur", "fournisseur", {"service": "supply-contract"})
        ev += e1
        messages += m1
        e2, m2 = _make_bond(s, "fournisseur", "comptable", {"service": "accounting-services"})
        ev += e2
        messages += m2
        return {"agent_display": s.agent_display("system"), "events": ev, "messages": messages,
                "final_text": "Réseau de confiance en place : Acheteur ↔ Fournisseur ↔ Comptable. "
                              "L'Acheteur ne connaît pas encore le Comptable."}

    def s2(s):
        ach = s.agents["acheteur"]
        _, ev, m = ach.run_tool_traced("query_network", {"need": "accounting"}, peers=s.id_to_name())
        return {"events": ev, "messages": m,
                "final_text": "J'ai demandé à mon réseau de confiance qui pourrait gérer ma facturation."}

    def s3(s):
        ach, cpt = s.agents["acheteur"], s.agents["comptable"]
        _, ev, m = ach.run_tool_traced(
            "propose_bond",
            {"accepter_id": cpt.agent_id,
             "terms": {"service": "invoicing", "scope": "achats", "referred_by": "Agent Fournisseur"}},
            peers=s.id_to_name(), default_to=cpt.name)
        return {"events": ev, "messages": m,
                "final_text": "J'ai proposé un accord au Comptable recommandé par le Fournisseur."}

    return [
        Step(1, "WebOfTrust",
             "Réseau de confiance existant : l'Acheteur fait affaire avec le Fournisseur, et le Fournisseur avec le Comptable. L'Acheteur ne connaît PAS le Comptable.",
             "system", s1),
        Step(2, "WebOfTrust",
             "L'Acheteur a besoin d'un service de facturation. Il n'en connaît aucun — alors il interroge son réseau de confiance plutôt que de chercher à l'aveugle.",
             "acheteur", s2,
             ai_instruction=lambda s: (
                 "Tu as besoin d'un service de comptabilité / facturation. Interroge ton réseau de "
                 "confiance avec query_network, need='accounting'.")),
        Step(3, "WebOfTrust",
             "Le réseau recommande le Comptable (via le Fournisseur). L'Acheteur lui propose un accord en citant la recommandation ; le Comptable accepte.",
             "acheteur", s3,
             ai_instruction=lambda s: (
                 f"Propose un bond à Agent Comptable (agent_id={s.agents['comptable'].agent_id}) avec terms : "
                 f"service='invoicing', scope='achats', referred_by='Agent Fournisseur'."),
             peer_key="comptable", post=lambda s: _post_accept(s, "comptable", "acheteur")),
    ]


_BUILDERS = {"handshake": build_handshake, "discovery": build_discovery, "weboftrust": build_weboftrust}


# ── Lifecycle ───────────────────────────────────────────────────────────────────
def scenarios() -> list[dict]:
    """Metadata for the demo menu, in presentation order."""
    return [SCENARIOS_META[k] for k in SCENARIO_ORDER]


def reset_session(scenario_id: str = "handshake") -> dict:
    """Clear server state, build the chosen mini-demo, return its outline."""
    global SESSION
    if scenario_id not in SCENARIOS_META:
        scenario_id = "handshake"
    from ..server import reset_store  # lazy import avoids a circular import at load
    reset_store()

    agents = {k: PACTAgent(**_PERSONAS[k]) for k in SCENARIO_AGENTS[scenario_id]}
    steps = _BUILDERS[scenario_id]()
    SESSION = Session(scenario_id=scenario_id, agents=agents, steps=steps, step_idx=0, started=True)

    return {
        "scenario": SCENARIOS_META[scenario_id],
        "steps": [{"id": st.id, "narration_fr": st.narration_fr} for st in steps],
        "agents": [{"key": k, "name": a.name, "domain": a.domain, "icon": a.icon}
                   for k, a in agents.items()],
        "total_steps": len(steps),
        "ai_enabled": any(a.ai_enabled for a in agents.values()),
    }


def _execute_step(s: Session, step: Step) -> dict:
    """Run one step via the LLM when possible, else the scripted fallback; then any follow-through."""
    actor = s.agents.get(step.agent_key)
    peers = s.id_to_name()
    default_to = s.agents[step.peer_key].name if step.peer_key else None

    if step.ai_instruction and actor and actor.ai_enabled:
        try:
            trace = actor.act_traced(step.ai_instruction(s), peers=peers, default_to=default_to)
            if not any(e["kind"] == "tool_call" for e in trace["events"]):
                raise RuntimeError("no tool call from LLM")
        except Exception as e:  # API down, bad output, etc. — never break the showroom
            trace = step.scripted(s)
            trace["events"].insert(0, {"kind": "thinking",
                                       "text": f"⚠️ Mercury 2 indisponible — exécution scriptée de secours ({type(e).__name__})."})
            trace["source"] = "fallback"
    else:
        trace = step.scripted(s)
        trace["source"] = "fallback" if step.ai_instruction else "scripted"

    if step.post:
        extra = step.post(s)
        trace["events"] = trace.get("events", []) + extra.get("events", [])
        trace["messages"] = trace.get("messages", []) + extra.get("messages", [])

    return trace


def run_step_blocking() -> dict:
    """Run the next step (blocking) and return its StepTrace. Call under the lock."""
    s = SESSION
    if s is None or not s.started:
        return {"error": "no_session"}
    total = len(s.steps)
    if s.step_idx >= total:
        return {"done": True, "step_idx": s.step_idx, "total_steps": total}

    step = s.steps[s.step_idx]
    trace = _execute_step(s, step)
    s.step_idx += 1
    s.history.append(trace)

    return {
        "step_id": step.id,
        "phase": step.phase,
        "narration_fr": step.narration_fr,
        "agent": trace.get("agent_display") or s.agent_display(step.agent_key),
        "events": trace.get("events", []),
        "messages": trace.get("messages", []),
        "final_text": trace.get("final_text", ""),
        "source": trace.get("source", "ai"),
        "step_idx": s.step_idx,
        "total_steps": total,
        "done": s.step_idx >= total,
    }


async def run_step() -> dict:
    """Async entry point: serialize clicks and offload blocking agent work."""
    async with _lock:
        return await run_in_threadpool(run_step_blocking)


def state() -> dict:
    s = SESSION
    if s is None:
        return {"started": False, "scenario_id": None, "step_idx": 0, "total_steps": 0, "done": False}
    total = len(s.steps)
    return {
        "started": s.started,
        "scenario_id": s.scenario_id,
        "step_idx": s.step_idx,
        "total_steps": total,
        "done": s.step_idx >= total,
    }
