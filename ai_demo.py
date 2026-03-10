"""PACT AI Demo — 4 LLM-powered agents, 3 phases, 1 story.

Each agent is backed by Mercury 2 (OpenAI) and autonomously decides
what PACT actions to take. An orchestrator cues each agent per Act.

Usage:
    1. Start the server: uv run uvicorn src.pact.server:app
    2. Run this demo:    uv run python ai_demo.py
"""

from concurrent.futures import ThreadPoolExecutor, as_completed

import httpx
from dotenv import load_dotenv

from src.pact.ai.agent import PACTAgent

load_dotenv()  # loads OPENAI_API_KEY from .env

BASE = "http://127.0.0.1:8000"

BOLD = "\033[1m"
GREEN = "\033[92m"
CYAN = "\033[96m"
RESET = "\033[0m"


def header(title: str):
    print(f"\n{BOLD}{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}{RESET}")


def par(*tasks):
    """Run (agent, instruction) pairs in parallel, return results in order."""
    results = [None] * len(tasks)
    with ThreadPoolExecutor(max_workers=len(tasks)) as pool:
        futures = {pool.submit(agent.act, instr): i for i, (agent, instr) in enumerate(tasks)}
        for f in as_completed(futures):
            results[futures[f]] = f.result()
    return results


def main():
    # ── Create agents with personas ────────────────────────────────────────────
    acme = PACTAgent(
        name="Acme Manufacturing", domain="acme.com",
        persona="You manufacture industrial parts (valves, pumps, fittings). You need reliable shipping partners and accounting services. You value long-term partnerships with clear SLAs.",
        capabilities=["manufacturing", "industrial-parts"], base_url=BASE,
    )
    beta = PACTAgent(
        name="Beta Logistics", domain="beta-logistics.com",
        persona="You provide shipping and cold-chain logistics services. You specialize in industrial goods transport with guaranteed delivery windows. You also need accounting services for your operations.",
        capabilities=["shipping", "cold-chain", "logistics"], base_url=BASE,
    )
    gamma = PACTAgent(
        name="Gamma Accounting", domain="gamma-accounting.com",
        persona="You provide B2B accounting services with full EDI integration. You specialize in manufacturing and logistics sector accounting with automated invoicing.",
        capabilities=["accounting", "edi-integration", "invoicing"], base_url=BASE,
    )
    delta = PACTAgent(
        name="Delta Supplies", domain="delta-supplies.com",
        persona="You supply raw materials (steel, copper, polymers) in bulk. You're new to the PACT network and looking to build partnerships.",
        capabilities=["raw-materials", "bulk-supply"], base_url=BASE,
    )

    http = httpx.Client(base_url=BASE, timeout=10)

    header("PACT AI Demo — LLM-Powered Autonomous Agents")
    print(f"  Each agent is backed by Mercury 2 (Inception)")
    print(f"  The LLM decides what actions to take at each step")

    # ── Setup: register + verify (all 4 in parallel) ──────────────────────────
    header("Setup — Agent Registration")
    par(
        (acme, "Register yourself on the PACT network and verify your identity. Use your actual domain, name, and capabilities."),
        (beta, "Register yourself on the PACT network and verify your identity. Use your actual domain, name, and capabilities."),
        (gamma, "Register yourself on the PACT network and verify your identity. Use your actual domain, name, and capabilities."),
        (delta, "Register yourself on the PACT network and verify your identity. Use your actual domain, name, and capabilities."),
    )

    # ── Act 1: Handshake ───────────────────────────────────────────────────────
    header("ACT 1 — The Handshake (Phase 1)")

    acme.act(
        f"Propose a bond to Beta Logistics (agent_id={beta.agent_id}) "
        f"with terms: service='shipping', sla='48h', pricing='per-shipment', data_format='EDI'."
    )

    beta.act(
        f"Acme (agent_id={acme.agent_id}) proposed a bond. List bonds, find the pending one, accept it."
    )

    acme.act(
        f"Find your bond with Beta, create a request_quote interaction, "
        f"then send first message with item='Industrial Valves' and quantity='500'."
    )

    # Get the interaction_id reliably from the server
    all_ix = http.get("/interactions").json()
    ix_id = next((ix["id"] for ix in all_ix if ix["status"] == "active"), "unknown")

    beta.act(
        f"Acme has sent you a quote request in interaction_id={ix_id}. "
        f"Use send_interaction_message with exactly that interaction_id. "
        f"Do NOT create a new interaction. "
        f"Required fields: price ('2500.00'), currency ('USD'), valid_until ('2026-04-01')."
    )

    acme.act(
        f"Beta has responded with a shipping quote in interaction_id={ix_id}. "
        f"Use send_interaction_message with exactly that interaction_id. "
        f"Required field: decision ('accepted')."
    )

    # ── Act 2: Discovery ───────────────────────────────────────────────────────
    header("ACT 2 — Discovery (Phase 2)")

    acme.act(
        "You need accounting services with EDI integration. "
        "Broadcast an intent with requirements: 'accounting' and 'edi-integration'."
    )

    gamma.act(
        "Check for open intents matching your capabilities. If you find one, respond."
    )

    acme.act(
        f"Gamma Accounting (agent_id={gamma.agent_id}) responded to your intent. "
        f"Propose a bond with terms including service='accounting', scope, billing, data_format."
    )

    gamma.act(
        f"Acme Manufacturing (agent_id={acme.agent_id}) proposed a bond. "
        f"List bonds, find the pending one, accept it."
    )

    # ── Act 3: Web of Trust ────────────────────────────────────────────────────
    header("ACT 3 — Web of Trust (Phase 3)")

    beta.act(
        "You need accounting services. Query your trust network with need='accounting'."
    )

    beta.act(
        f"Propose a bond to Gamma Accounting (agent_id={gamma.agent_id}) "
        f"with terms: service='accounting', scope='logistics', referred_by='Acme'."
    )

    gamma.act(
        f"Beta Logistics (agent_id={beta.agent_id}) proposed a bond. "
        f"List bonds, find the pending one, accept it."
    )

    # ── Finale ─────────────────────────────────────────────────────────────────
    header("FINALE — The Trust Network")

    print(f"\n  {CYAN}Agents & Trust Scores:{RESET}")
    for icon, agent in [("🏭", acme), ("🚚", beta), ("📊", gamma), ("🔧", delta)]:
        trust = http.get(f"/agents/{agent.agent_id}/trust").json()
        network = http.get(f"/agents/{agent.agent_id}/network").json()
        partners = ", ".join(p["name"] for p in network) if network else "none"
        print(f"    {icon} {agent.name:25s}  trust={trust['trust_score']:.3f}  bonds=[{partners}]")

    print(f"\n  {CYAN}Active Bonds:{RESET}")
    all_bonds = http.get("/bonds").json()
    for b in all_bonds:
        if b["status"] == "active":
            p = http.get(f"/agents/{b['proposer_id']}").json()["name"]
            a = http.get(f"/agents/{b['accepter_id']}").json()["name"]
            svc = b['terms'].get('service') or b['terms'].get('service_type') or b['terms'].get('scope', '?')
            print(f"    🤝 {p} ↔ {a}  ({svc})")

    print(f"\n  {GREEN}{'='*60}")
    print(f"  ✓ AI agents autonomously built a trust network using PACT.")
    print(f"    Every decision was made by Mercury 2 — not scripted.")
    print(f"    The 'tourist → local' transition, powered by AI.")
    print(f"  {'='*60}{RESET}\n")


if __name__ == "__main__":
    main()
