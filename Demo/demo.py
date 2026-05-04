"""PACT Demo — 4 agents voyage, 3 mécanismes, 1 voyage à Tokyo."""

import httpx
from pact.crypto import generate_keypair, sign

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


# ── Génération des paires de clés ──────────────────────────────────────────────
vol_sk, vol_pk = generate_keypair()
hotel_sk, hotel_pk = generate_keypair()
voiture_sk, voiture_pk = generate_keypair()
nf_sk, nf_pk = generate_keypair()

# ══════════════════════════════════════════════════════════════════════════════
header("PACT — Protocole de Coordination & Confiance entre Agents")
# ══════════════════════════════════════════════════════════════════════════════

print(f"  {CYAN}Scénario : organiser un voyage à Tokyo avec 4 agents IA autonomes.{RESET}")
print(f"  {CYAN}Chacun est expert dans son domaine — aucun ne se connaît au départ.{RESET}\n")

# ── Enregistrement des agents ──────────────────────────────────────────────────
header("Enregistrement des agents")

vol = c.post("/agents/register", json={
    "domain": "vol-agent.ai", "name": "Agent Vol",
    "public_key": vol_pk, "capabilities": ["flight-booking", "travel"],
}).json()
step("✈️", f"Agent Vol enregistré — id={vol['id']}")

hotel = c.post("/agents/register", json={
    "domain": "hotel-agent.ai", "name": "Agent Hôtel",
    "public_key": hotel_pk, "capabilities": ["accommodation", "hospitality"],
}).json()
step("🏨", f"Agent Hôtel enregistré — id={hotel['id']}")

voiture = c.post("/agents/register", json={
    "domain": "voiture-agent.ai", "name": "Agent Location Voiture",
    "public_key": voiture_pk, "capabilities": ["car-rental", "mobility"],
}).json()
step("🚗", f"Agent Location Voiture enregistré — id={voiture['id']}")

nf = c.post("/agents/register", json={
    "domain": "notes-frais-agent.ai", "name": "Agent Notes de Frais",
    "public_key": nf_pk, "capabilities": ["expense-management", "accounting", "reimbursement"],
}).json()
step("💳", f"Agent Notes de Frais enregistré — id={nf['id']}")

for agent in [vol, hotel, voiture, nf]:
    c.post(f"/agents/{agent['id']}/verify")
step("✓", "Tous les agents vérifiés\n")

# ── Bond préexistant Notes de frais ↔ Vol ─────────────────────────────────────
step("🔗", "Notes de Frais et Vol travaillent déjà ensemble depuis longtemps...")
terms_nv = {"service": "expense-audit", "scope": "flight expenses", "billing": "monthly"}
bond_nv = c.post("/bonds/propose", json={
    "proposer_id": nf["id"], "accepter_id": vol["id"],
    "terms": terms_nv, "signature": sign_terms(terms_nv, nf_sk),
}).json()
bond_nv = c.post(f"/bonds/{bond_nv['id']}/accept", json={
    "signature": sign_terms(terms_nv, vol_sk),
}).json()
step("✓", f"Bond actif — Notes de Frais ↔ Vol (audit des dépenses)\n")


# ══════════════════════════════════════════════════════════════════════════════
header("ACTE 1 — Formaliser une relation (Mécanisme 1)")
# ══════════════════════════════════════════════════════════════════════════════

print(f"  {YELLOW}Le Vol et l'Hôtel ont déjà collaboré. Ils formalisent leur relation :")
print(f"  conditions, délais, format des échanges. Un contrat numérique infalsifiable.{RESET}\n")

step("📝", "Vol propose un bond à Hôtel (coordination de voyage)...")
terms_vh = {
    "service": "travel-coordination",
    "sla": "24h confirmation",
    "data_format": "JSON",
    "scope": "client bookings",
}
bond_vh = c.post("/bonds/propose", json={
    "proposer_id": vol["id"], "accepter_id": hotel["id"],
    "terms": terms_vh, "signature": sign_terms(terms_vh, vol_sk),
}).json()
step("📋", f"Bond proposé — id={bond_vh['id']}, status={bond_vh['status']}")

step("🤝", "Hôtel accepte le bond...")
bond_vh = c.post(f"/bonds/{bond_vh['id']}/accept", json={
    "signature": sign_terms(terms_vh, hotel_sk),
}).json()
step("✓", f"Bond actif — Vol ↔ Hôtel, status={bond_vh['status']}")

# Réservation hôtel via interaction structurée
step("\n📨", "Vol informe Hôtel de la date d'arrivée et demande une réservation...")
ix = c.post("/interactions/create", json={
    "bond_id": bond_vh["id"], "template": "request_booking", "initiator_id": vol["id"],
}).json()

booking_req = {
    "item": "Chambre Tokyo",
    "check_in": "2026-03-12",
    "check_out": "2026-03-15",
    "guests": "1",
}
c.post(f"/interactions/{ix['id']}/message", json={
    "sender_id": vol["id"], "data": booking_req, "signature": sign_data(booking_req, vol_sk),
})
step("→", "Vol : 'Chambre à Tokyo, du 12 au 15 mars, 1 voyageur'")

booking_resp = {
    "booking_id": "HTL-7842",
    "total_price": "450.00",
    "currency": "EUR",
}
c.post(f"/interactions/{ix['id']}/message", json={
    "sender_id": hotel["id"], "data": booking_resp, "signature": sign_data(booking_resp, hotel_sk),
})
step("←", "Hôtel : 'Réservation HTL-7842 confirmée, 450 EUR'")

decision = {"decision": "accepted"}
result = c.post(f"/interactions/{ix['id']}/message", json={
    "sender_id": vol["id"], "data": decision, "signature": sign_data(decision, vol_sk),
}).json()
step("✓", f"Vol valide la réservation — interaction {result['interaction_status']}\n")


# ══════════════════════════════════════════════════════════════════════════════
header("ACTE 2 — Se trouver automatiquement (Mécanisme 2)")
# ══════════════════════════════════════════════════════════════════════════════

print(f"  {YELLOW}Le voyage est étendu d'une semaine. On a besoin d'une voiture.")
print(f"  Personne ne connaît encore d'agent location. Le Vol diffuse un signal.{RESET}\n")

step("📡", "Vol diffuse : 'je cherche un agent spécialisé en mobilité'")
intent = c.post("/intents/broadcast", json={
    "agent_id": vol["id"],
    "need": "location de voiture",
    "requirements": ["car-rental", "mobility"],
}).json()
step("📋", f"Intent diffusé — id={intent['id']}")

step("🔍", "Voiture vérifie les signaux qui correspondent à ses capacités...")
matches = c.get(f"/intents/matching/{voiture['id']}").json()
step("✓", f"{len(matches)} signal(aux) compatible(s) trouvé(s)")

step("💬", "Voiture répond : 'Location flexible, assurance incluse'")
c.post(f"/intents/{intent['id']}/respond", json={
    "agent_id": voiture["id"],
    "message": "Nous proposons de la location flexible avec assurance tous risques incluse.",
})

step("\n📝", "Vol et Voiture établissent un bond...")
terms_vv = {
    "service": "car-rental",
    "duration": "weekly",
    "insurance": "included",
}
bond_vv = c.post("/bonds/propose", json={
    "proposer_id": vol["id"], "accepter_id": voiture["id"],
    "terms": terms_vv, "signature": sign_terms(terms_vv, vol_sk),
}).json()
bond_vv = c.post(f"/bonds/{bond_vv['id']}/accept", json={
    "signature": sign_terms(terms_vv, voiture_sk),
}).json()
step("✓", f"Bond actif — Vol ↔ Voiture (sans intervention humaine)\n")


# ══════════════════════════════════════════════════════════════════════════════
header("ACTE 3 — La recommandation (Mécanisme 3)")
# ══════════════════════════════════════════════════════════════════════════════

print(f"  {YELLOW}Notes de Frais doit récupérer les factures de l'hôtel. Plutôt que")
print(f"  de chercher dans le vide, il interroge son réseau de confiance.{RESET}\n")

step("🔎", "Notes de Frais : 'est-ce que quelqu'un connaît un agent hôtelier ?'")
recs = c.post("/network/query", json={
    "agent_id": nf["id"], "need": "hospitality",
}).json()

for rec in recs:
    step("⭐", f"Recommandation : {rec['agent_name']} (via {rec['referred_by_name']}, score de confiance={rec['trust_score']:.2f})")

if recs:
    recommended = recs[0]
    step("\n📝", f"Notes de Frais propose un bond à {recommended['agent_name']} (recommandé par {recommended['referred_by_name']})...")
    terms_nh = {
        "service": "invoice-retrieval",
        "scope": "client expenses",
        "referred_by": recommended["referred_by_name"],
    }
    bond_nh = c.post("/bonds/propose", json={
        "proposer_id": nf["id"], "accepter_id": recommended["agent_id"],
        "terms": terms_nh, "signature": sign_terms(terms_nh, nf_sk),
    }).json()
    bond_nh = c.post(f"/bonds/{bond_nh['id']}/accept", json={
        "signature": sign_terms(terms_nh, hotel_sk),
    }).json()
    step("✓", f"Bond actif — Notes de Frais ↔ Hôtel (créé par recommandation)\n")
else:
    step("⚠️", "Aucune recommandation trouvée — vérifier la chaîne de bonds\n")


# ══════════════════════════════════════════════════════════════════════════════
header("FINALE — Le réseau de confiance")
# ══════════════════════════════════════════════════════════════════════════════

print(f"  {CYAN}Agents & scores de confiance :{RESET}")
for agent_info in [("✈️", vol), ("🏨", hotel), ("🚗", voiture), ("💳", nf)]:
    icon, a = agent_info
    trust = c.get(f"/agents/{a['id']}/trust").json()
    network = c.get(f"/agents/{a['id']}/network").json()
    partners = ", ".join(p["name"] for p in network) if network else "aucun"
    print(f"    {icon} {a['name']:28s}  confiance={trust['trust_score']:.3f}  partenaires=[{partners}]")

print(f"\n  {CYAN}Bonds actifs :{RESET}")
all_bonds = c.get("/bonds").json()
for b in all_bonds:
    if b["status"] == "active":
        p = c.get(f"/agents/{b['proposer_id']}").json()["name"]
        a = c.get(f"/agents/{b['accepter_id']}").json()["name"]
        print(f"    🤝 {p} ↔ {a}  ({b['terms'].get('service', '?')})")

print(f"\n  {GREEN}{'='*60}")
print(f"  ✓ Un voyage à Tokyo organisé par 4 agents qui se sont trouvés")
print(f"    et qui se font confiance.")
print(f"    Aucun humain n'a coordonné. Tout est tracé, signé, auditable.")
print(f"  {'='*60}{RESET}\n")
