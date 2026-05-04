"""PACT AI Demo — 4 agents voyage LLM, 3 mécanismes, 1 voyage à Tokyo.

Chaque agent est piloté par Mercury 2 (Inception) et décide de façon autonome
quelles actions PACT entreprendre. Un orchestrateur donne juste l'objectif de
chaque acte.

Usage :
    1. Démarrer le serveur :    uv run uvicorn src.pact.server:app
    2. Lancer la démo :          uv run python Demo/ai_demo.py
"""

from concurrent.futures import ThreadPoolExecutor, as_completed

import httpx
from dotenv import load_dotenv

from pact.ai.agent import PACTAgent

load_dotenv()  # charge INCEPTION_API_KEY depuis .env

BASE = "http://127.0.0.1:8000"

BOLD = "\033[1m"
GREEN = "\033[92m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def header(title: str):
    print(f"\n{BOLD}{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}{RESET}")


def par(*tasks):
    """Exécute des paires (agent, instruction) en parallèle."""
    results = [None] * len(tasks)
    with ThreadPoolExecutor(max_workers=len(tasks)) as pool:
        futures = {pool.submit(agent.act, instr): i for i, (agent, instr) in enumerate(tasks)}
        for f in as_completed(futures):
            results[futures[f]] = f.result()
    return results


def main():
    # ── Création des agents avec leurs personas ────────────────────────────────
    vol = PACTAgent(
        name="Agent Vol", domain="vol-agent.ai",
        persona="Tu es un agent autonome spécialisé dans la réservation de vols. "
                "Tu coordonnes avec d'autres agents voyage (hôtels, locations) pour "
                "organiser des voyages complets de bout en bout. Tu valorises les "
                "partenariats long-terme avec des SLA clairs sur la confirmation "
                "des réservations.",
        capabilities=["flight-booking", "travel"], base_url=BASE,
    )
    hotel = PACTAgent(
        name="Agent Hôtel", domain="hotel-agent.ai",
        persona="Tu es un agent autonome spécialisé dans la réservation d'hébergements. "
                "Tu travailles avec des agents de voyage pour confirmer rapidement les "
                "chambres et fournir un identifiant de réservation. Tu fournis aussi "
                "des factures pour les services de notes de frais.",
        capabilities=["accommodation", "hospitality"], base_url=BASE,
    )
    voiture = PACTAgent(
        name="Agent Location Voiture", domain="voiture-agent.ai",
        persona="Tu es un agent autonome spécialisé dans la location de voitures. "
                "Tu offres des solutions flexibles avec assurance incluse. Tu es "
                "nouveau sur le réseau PACT et tu cherches à établir des partenariats "
                "avec des agents de voyage.",
        capabilities=["car-rental", "mobility"], base_url=BASE,
    )
    nf = PACTAgent(
        name="Agent Notes de Frais", domain="notes-frais-agent.ai",
        persona="Tu es un agent autonome qui gère les notes de frais et les "
                "remboursements. Tu travailles déjà avec des agents de vol pour "
                "auditer les dépenses. Tu as besoin de récupérer des factures auprès "
                "des hôtels et autres prestataires de voyage.",
        capabilities=["expense-management", "accounting", "reimbursement"], base_url=BASE,
    )

    http = httpx.Client(base_url=BASE, timeout=10)

    header("PACT AI Demo — Agents autonomes pilotés par LLM")
    print(f"  {CYAN}Scénario : organiser un voyage à Tokyo{RESET}")
    print(f"  {CYAN}Chaque agent est piloté par Mercury 2 (Inception){RESET}")
    print(f"  {CYAN}Le LLM décide quelles actions entreprendre à chaque étape{RESET}")

    # ── Setup : enregistrement (les 4 en parallèle) ────────────────────────────
    header("Setup — Enregistrement des agents")
    par(
        (vol, "Enregistre-toi sur le réseau PACT et vérifie ton identité. Utilise ton domaine, ton nom et tes capacités."),
        (hotel, "Enregistre-toi sur le réseau PACT et vérifie ton identité. Utilise ton domaine, ton nom et tes capacités."),
        (voiture, "Enregistre-toi sur le réseau PACT et vérifie ton identité. Utilise ton domaine, ton nom et tes capacités."),
        (nf, "Enregistre-toi sur le réseau PACT et vérifie ton identité. Utilise ton domaine, ton nom et tes capacités."),
    )

    # ── Bond préexistant Notes de frais ↔ Vol ──────────────────────────────────
    header("Setup — Relation préexistante Notes de Frais ↔ Vol")
    print(f"  {YELLOW}Notes de Frais audite déjà les dépenses du Vol depuis longtemps.{RESET}")

    nf.act(
        f"Propose un bond à Agent Vol (agent_id={vol.agent_id}) avec terms : "
        f"service='expense-audit', scope='flight expenses', billing='monthly'."
    )
    vol.act(
        f"Notes de Frais (agent_id={nf.agent_id}) a proposé un bond. "
        f"List bonds, trouve le bond en attente, accepte-le."
    )

    # ── Acte 1 : Formaliser une relation ───────────────────────────────────────
    header("ACTE 1 — Formaliser une relation (Mécanisme 1)")
    print(f"  {YELLOW}Vol et Hôtel formalisent leur relation : un contrat numérique signé.{RESET}")

    vol.act(
        f"Propose un bond à Agent Hôtel (agent_id={hotel.agent_id}) avec terms : "
        f"service='travel-coordination', sla='24h confirmation', data_format='JSON', scope='client bookings'."
    )

    hotel.act(
        f"Agent Vol (agent_id={vol.agent_id}) a proposé un bond. "
        f"List bonds, trouve le bond en attente avec Vol, accepte-le."
    )

    vol.act(
        f"Trouve ton bond avec Agent Hôtel (agent_id={hotel.agent_id}), crée une "
        f"interaction avec template='request_booking', puis envoie le premier "
        f"message avec item='Chambre Tokyo', check_in='2026-03-12', "
        f"check_out='2026-03-15', guests='1'."
    )

    # Récupère l'interaction_id côté serveur
    all_ix = http.get("/interactions").json()
    ix_id = next((ix["id"] for ix in all_ix if ix["status"] == "active"), "unknown")

    hotel.act(
        f"Vol t'a envoyé une demande de réservation dans interaction_id={ix_id}. "
        f"Utilise send_interaction_message avec exactement cet interaction_id. "
        f"NE crée PAS de nouvelle interaction. "
        f"Champs requis : booking_id ('HTL-7842'), total_price ('450.00'), currency ('EUR')."
    )

    vol.act(
        f"Hôtel a confirmé la réservation dans interaction_id={ix_id}. "
        f"Utilise send_interaction_message avec exactement cet interaction_id. "
        f"Champ requis : decision ('accepted')."
    )

    # ── Acte 2 : Se trouver automatiquement ────────────────────────────────────
    header("ACTE 2 — Se trouver automatiquement (Mécanisme 2)")
    print(f"  {YELLOW}Le voyage est étendu d'une semaine. Le Vol cherche un agent mobilité.{RESET}")

    vol.act(
        "Tu as besoin de trouver un agent de location de voiture. "
        "Diffuse un intent avec need='location de voiture' et "
        "requirements : 'car-rental' et 'mobility'."
    )

    voiture.act(
        "Vérifie les intents ouverts qui correspondent à tes capacités. "
        "Si tu en trouves un, réponds avec un message décrivant ton offre."
    )

    vol.act(
        f"Agent Location Voiture (agent_id={voiture.agent_id}) a répondu à ton intent. "
        f"Propose-lui un bond avec terms : service='car-rental', duration='weekly', insurance='included'."
    )

    voiture.act(
        f"Agent Vol (agent_id={vol.agent_id}) a proposé un bond. "
        f"List bonds, trouve le bond en attente, accepte-le."
    )

    # ── Acte 3 : La recommandation ─────────────────────────────────────────────
    header("ACTE 3 — La recommandation (Mécanisme 3)")
    print(f"  {YELLOW}Notes de Frais demande à son réseau de confiance : 'tu connais un hôtelier ?'{RESET}")

    nf.act(
        "Tu as besoin de récupérer des factures auprès d'un agent hôtelier. "
        "Interroge ton réseau de confiance avec query_network, need='hospitality'."
    )

    nf.act(
        f"Propose un bond à Agent Hôtel (agent_id={hotel.agent_id}) avec terms : "
        f"service='invoice-retrieval', scope='client expenses', referred_by='Agent Vol'."
    )

    hotel.act(
        f"Agent Notes de Frais (agent_id={nf.agent_id}) a proposé un bond. "
        f"List bonds, trouve le bond en attente, accepte-le."
    )

    # ── Finale ─────────────────────────────────────────────────────────────────
    header("FINALE — Le réseau de confiance")

    print(f"\n  {CYAN}Agents & scores de confiance :{RESET}")
    for icon, agent in [("✈️", vol), ("🏨", hotel), ("🚗", voiture), ("💳", nf)]:
        trust = http.get(f"/agents/{agent.agent_id}/trust").json()
        network = http.get(f"/agents/{agent.agent_id}/network").json()
        partners = ", ".join(p["name"] for p in network) if network else "aucun"
        print(f"    {icon} {agent.name:28s}  confiance={trust['trust_score']:.3f}  partenaires=[{partners}]")

    print(f"\n  {CYAN}Bonds actifs :{RESET}")
    all_bonds = http.get("/bonds").json()
    for b in all_bonds:
        if b["status"] == "active":
            p = http.get(f"/agents/{b['proposer_id']}").json()["name"]
            a = http.get(f"/agents/{b['accepter_id']}").json()["name"]
            svc = b['terms'].get('service') or b['terms'].get('service_type') or b['terms'].get('scope', '?')
            print(f"    🤝 {p} ↔ {a}  ({svc})")

    print(f"\n  {GREEN}{'='*60}")
    print(f"  ✓ Un voyage à Tokyo organisé par 4 agents IA autonomes.")
    print(f"    Mercury 2 a décidé toutes les actions. Aucun script.")
    print(f"    Aucun humain dans la boucle.")
    print(f"  {'='*60}{RESET}\n")


if __name__ == "__main__":
    main()
