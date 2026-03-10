"""PACT Demo — 4 agents, 3 phases, 1 story."""

import httpx
from src.pact.crypto import generate_keypair, sign

BASE = "http://127.0.0.1:8000"
c = httpx.Client(base_url=BASE, timeout=10)

BOLD = "\033[1m"
GREEN = "\033[92m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def header(title: str):
    print(f"\n{BOLD}{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}{RESET}\n")


def step(icon: str, msg: str):
    print(f"  {icon}  {msg}")


def sign_terms(terms: dict, private_key: str) -> str:
    return sign(str(sorted(terms.items())), private_key)


def sign_data(data: dict, private_key: str) -> str:
    return sign(str(sorted(data.items())), private_key)


# ── Generate keypairs ──────────────────────────────────────────────────────────
acme_sk, acme_pk = generate_keypair()
beta_sk, beta_pk = generate_keypair()
gamma_sk, gamma_pk = generate_keypair()
delta_sk, delta_pk = generate_keypair()

# ══════════════════════════════════════════════════════════════════════════════
header("PACT PoC — Protocol for Agent Coordination & Trust")
# ══════════════════════════════════════════════════════════════════════════════

# ── Register all agents ────────────────────────────────────────────────────────
header("Registering Agents")

acme = c.post("/agents/register", json={"domain": "acme.com", "name": "Acme Manufacturing", "public_key": acme_pk, "capabilities": ["manufacturing", "industrial-parts"]}).json()
step("🏭", f"Acme Manufacturing registered — id={acme['id']}")

beta = c.post("/agents/register", json={"domain": "beta-logistics.com", "name": "Beta Logistics", "public_key": beta_pk, "capabilities": ["shipping", "cold-chain", "logistics"]}).json()
step("🚚", f"Beta Logistics registered — id={beta['id']}")

gamma = c.post("/agents/register", json={"domain": "gamma-accounting.com", "name": "Gamma Accounting", "public_key": gamma_pk, "capabilities": ["accounting", "edi-integration", "invoicing"]}).json()
step("📊", f"Gamma Accounting registered — id={gamma['id']}")

delta = c.post("/agents/register", json={"domain": "delta-supplies.com", "name": "Delta Supplies", "public_key": delta_pk, "capabilities": ["raw-materials", "bulk-supply"]}).json()
step("🔧", f"Delta Supplies registered — id={delta['id']}")

# Verify all agents
for agent in [acme, beta, gamma, delta]:
    c.post(f"/agents/{agent['id']}/verify")
step("✓", "All agents verified\n")


# ══════════════════════════════════════════════════════════════════════════════
header("ACT 1 — The Handshake (Phase 1)")
# ══════════════════════════════════════════════════════════════════════════════

step("📝", "Acme proposes a bond to Beta with shipping terms...")
terms = {"service": "shipping", "sla": "48h delivery", "pricing": "negotiated rates", "data_format": "EDI"}
bond_ab = c.post("/bonds/propose", json={
    "proposer_id": acme["id"], "accepter_id": beta["id"],
    "terms": terms, "signature": sign_terms(terms, acme_sk),
}).json()
step("📋", f"Bond proposed — id={bond_ab['id']}, status={bond_ab['status']}")

step("🤝", "Beta accepts the bond...")
bond_ab = c.post(f"/bonds/{bond_ab['id']}/accept", json={
    "signature": sign_terms(terms, beta_sk),
}).json()
step("✓", f"Bond active — id={bond_ab['id']}, status={bond_ab['status']}")

# Run a request_quote interaction
step("\n📨", "Acme requests a shipping quote from Beta...")
ix = c.post("/interactions/create", json={
    "bond_id": bond_ab["id"], "template": "request_quote", "initiator_id": acme["id"],
}).json()

quote_req = {"item": "Industrial Valves (500 units)", "quantity": "500"}
c.post(f"/interactions/{ix['id']}/message", json={
    "sender_id": acme["id"], "data": quote_req, "signature": sign_data(quote_req, acme_sk),
})
step("→", "Acme: 'Quote for 500 Industrial Valves'")

quote_resp = {"price": "2500.00", "currency": "USD", "valid_until": "2026-04-01"}
c.post(f"/interactions/{ix['id']}/message", json={
    "sender_id": beta["id"], "data": quote_resp, "signature": sign_data(quote_resp, beta_sk),
})
step("←", "Beta: '$2,500 USD, valid until April 1'")

decision = {"decision": "accepted"}
result = c.post(f"/interactions/{ix['id']}/message", json={
    "sender_id": acme["id"], "data": decision, "signature": sign_data(decision, acme_sk),
}).json()
step("✓", f"Acme accepts quote — interaction {result['interaction_status']}\n")


# ══════════════════════════════════════════════════════════════════════════════
header("ACT 2 — Discovery (Phase 2)")
# ══════════════════════════════════════════════════════════════════════════════

step("📡", "Acme broadcasts intent: 'I need accounting services with EDI integration'")
intent = c.post("/intents/broadcast", json={
    "agent_id": acme["id"],
    "need": "accounting services",
    "requirements": ["accounting", "edi-integration"],
}).json()
step("📋", f"Intent broadcast — id={intent['id']}")

step("🔍", "Gamma checks for matching intents...")
matches = c.get(f"/intents/matching/{gamma['id']}").json()
step("✓", f"Found {len(matches)} matching intent(s)")

step("💬", "Gamma responds: 'We offer full EDI-integrated accounting'")
c.post(f"/intents/{intent['id']}/respond", json={
    "agent_id": gamma["id"],
    "message": "We provide full EDI-integrated B2B accounting services with automated invoicing.",
})

step("\n📝", "Acme and Gamma establish a bond...")
terms_ag = {"service": "accounting", "scope": "B2B invoicing + EDI", "billing": "monthly"}
bond_ag = c.post("/bonds/propose", json={
    "proposer_id": acme["id"], "accepter_id": gamma["id"],
    "terms": terms_ag, "signature": sign_terms(terms_ag, acme_sk),
}).json()
bond_ag = c.post(f"/bonds/{bond_ag['id']}/accept", json={
    "signature": sign_terms(terms_ag, gamma_sk),
}).json()
step("✓", f"Bond active — Acme ↔ Gamma, id={bond_ag['id']}\n")


# ══════════════════════════════════════════════════════════════════════════════
header("ACT 3 — Web of Trust (Phase 3)")
# ══════════════════════════════════════════════════════════════════════════════

step("🔗", "Beta needs an accountant. Queries its trust network...")
recs = c.post("/network/query", json={
    "agent_id": beta["id"], "need": "accounting",
}).json()

for rec in recs:
    step("⭐", f"Recommendation: {rec['agent_name']} (via {rec['referred_by_name']}, trust={rec['trust_score']})")

if recs:
    recommended = recs[0]
    step("\n📝", f"Beta establishes bond with {recommended['agent_name']} (referral from {recommended['referred_by_name']})...")
    terms_bg = {"service": "accounting", "scope": "logistics invoicing", "referred_by": recommended["referred_by"]}
    bond_bg = c.post("/bonds/propose", json={
        "proposer_id": beta["id"], "accepter_id": recommended["agent_id"],
        "terms": terms_bg, "signature": sign_terms(terms_bg, beta_sk),
    }).json()
    bond_bg = c.post(f"/bonds/{bond_bg['id']}/accept", json={
        "signature": sign_terms(terms_bg, gamma_sk),
    }).json()
    step("✓", f"Bond active — Beta ↔ Gamma, id={bond_bg['id']}\n")


# ══════════════════════════════════════════════════════════════════════════════
header("FINALE — The Trust Network")
# ══════════════════════════════════════════════════════════════════════════════

print(f"  {CYAN}Agents & Trust Scores:{RESET}")
for agent_info in [("🏭", acme), ("🚚", beta), ("📊", gamma), ("🔧", delta)]:
    icon, a = agent_info
    trust = c.get(f"/agents/{a['id']}/trust").json()
    network = c.get(f"/agents/{a['id']}/network").json()
    partners = ", ".join(p["name"] for p in network) if network else "none"
    print(f"    {icon} {a['name']:25s}  trust={trust['trust_score']:.3f}  bonds=[{partners}]")

print(f"\n  {CYAN}Active Bonds:{RESET}")
all_bonds = c.get("/bonds").json()
for b in all_bonds:
    if b["status"] == "active":
        p = c.get(f"/agents/{b['proposer_id']}").json()["name"]
        a = c.get(f"/agents/{b['accepter_id']}").json()["name"]
        print(f"    🤝 {p} ↔ {a}  ({b['terms'].get('service', '?')})")

print(f"\n  {GREEN}{'='*60}")
print(f"  ✓ What started as 2 strangers is now a connected network.")
print(f"    The 'tourist → local' transition in action.")
print(f"  {'='*60}{RESET}\n")
