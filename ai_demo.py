"""PACT AI Demo — 4 LLM-powered agents, 3 phases, 1 story.

Each agent is backed by GPT-5-mini (OpenAI) and autonomously decides
what PACT actions to take. An orchestrator cues each agent per Act.

Usage:
    1. Start the server: uv run uvicorn src.pact.server:app
    2. Run this demo:    uv run python ai_demo.py
"""

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
    print(f"  Each agent is backed by GPT-5-mini (OpenAI)")
    print(f"  The LLM decides what actions to take at each step")

    # ── Setup: register + verify ───────────────────────────────────────────────
    header("Setup — Agent Registration")
    for agent in [acme, beta, gamma, delta]:
        agent.act("Register yourself on the PACT network and verify your identity. Use your actual domain, name, and capabilities.")

    # ── Act 1: Handshake ───────────────────────────────────────────────────────
    header("ACT 1 — The Handshake (Phase 1)")

    acme.act(
        f"You already work with Beta Logistics (agent_id={beta.agent_id}). "
        f"Propose a bond to them for shipping services. The terms dict MUST include a key called 'service' "
        f"(e.g. 'shipping'). Also include sla, pricing, and data_format keys."
    )

    beta.act(
        f"Acme Manufacturing (agent_id={acme.agent_id}) has proposed a bond to you. "
        f"List the bonds to find the pending proposal, then accept it."
    )

    acme_act1 = acme.act(
        f"You have an active bond with Beta Logistics. Find your bond with them, "
        f"then start a request_quote interaction. Then send the first message with "
        f"required fields: item (e.g. 'Industrial Valves') and quantity (e.g. '500'). "
        f"Return the interaction_id in your response."
    )

    # Extract interaction_id from Acme's response to pass to Beta
    import re
    ix_match = re.search(r'[a-f0-9]{8}', acme_act1.split("interaction")[1] if "interaction" in acme_act1 else "")
    ix_hint = f" The interaction_id is likely {ix_match.group()}" if ix_match else ""

    beta.act(
        f"Acme has sent you a quote request in an active interaction on your bond.{ix_hint}. "
        f"Use send_interaction_message with the SAME interaction_id that Acme used. "
        f"Do NOT create a new interaction. The required fields for this step are: "
        f"price (e.g. '2500.00'), currency (e.g. 'USD'), and valid_until (e.g. '2026-04-01')."
    )

    acme.act(
        f"Beta has responded with a shipping quote in the interaction.{ix_hint}. "
        f"Send your decision using send_interaction_message on the SAME interaction_id. "
        f"The only required field is 'decision' (e.g. 'accepted')."
    )

    # ── Act 2: Discovery ───────────────────────────────────────────────────────
    header("ACT 2 — Discovery (Phase 2)")

    acme.act(
        "You need accounting services with EDI integration for your manufacturing business. "
        "Broadcast an intent on the PACT network describing what you need. "
        "Use requirements tags that would match an accounting provider: 'accounting' and 'edi-integration'."
    )

    gamma.act(
        "Check if there are any open intents on the PACT network that match your capabilities. "
        "If you find a match, respond with a compelling message about your services."
    )

    acme.act(
        f"Gamma Accounting (agent_id={gamma.agent_id}) responded to your accounting intent. "
        f"They seem like a good fit. Propose a bond to them. "
        f"The terms dict MUST include a key called 'service' (value: 'accounting'). "
        f"Also include scope, billing, and data_format keys."
    )

    gamma.act(
        f"Acme Manufacturing (agent_id={acme.agent_id}) has proposed an accounting bond to you. "
        f"List bonds to find the pending proposal and accept it."
    )

    # ── Act 3: Web of Trust ────────────────────────────────────────────────────
    header("ACT 3 — Web of Trust (Phase 3)")

    beta.act(
        "You also need an accountant for your logistics operations. "
        "Instead of broadcasting, query your trust network for recommendations. "
        "Use query_network with need='accounting' (use the exact short tag, not a long description)."
    )

    beta.act(
        f"You received a recommendation for Gamma Accounting (agent_id={gamma.agent_id}) "
        f"through your trust network (referred by Acme). "
        f"Propose a bond to Gamma for accounting services. "
        f"The terms dict MUST include a key called 'service' (value: 'accounting'). "
        f"Also include scope and referred_by keys."
    )

    gamma.act(
        f"Beta Logistics (agent_id={beta.agent_id}) has proposed an accounting bond to you "
        f"(they were referred by Acme). List bonds to find and accept the pending proposal."
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
    print(f"    Every decision was made by GPT-5-mini — not scripted.")
    print(f"    The 'tourist → local' transition, powered by AI.")
    print(f"  {'='*60}{RESET}\n")


if __name__ == "__main__":
    main()
