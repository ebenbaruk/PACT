# PACT — Réunion de Suivi #1

**Date :** 20 mars 2026
**Projet :** PACT — Protocol for Agent Coordination & Trust
**Durée :** 10 minutes

---

## 1. Présentation du Projet

### Problème visé

Les agents IA savent interagir avec des humains, mais **il n'existe aucune infrastructure** pour qu'ils se découvrent, se fassent confiance et collaborent entre eux de manière structurée et sécurisée.

Chaque interaction inter-agents est un **one-shot** : l'agent cherche, compare, négocie depuis zéro — à chaque fois. C'est le **problème "touriste vs. local"** : les agents fonctionnent comme des touristes alors que le commerce B2B réel fonctionne comme des locaux (relations durables, prix pré-négociés, confiance construite dans le temps).

### Produit

**PACT** est un protocole de coordination léger (API REST + Dashboard) qui permet aux agents IA de :

1. **Se découvrir** — via des intentions structurées et du matching par capacités
2. **Établir la confiance** — via des bonds cryptographiquement signés (Ed25519)
3. **Collaborer** — via des templates d'interaction structurés (devis, commandes)
4. **Étendre leur réseau** — via des recommandations pair-à-pair (web of trust)

**Ce qui est livré aujourd'hui :**
- Serveur API FastAPI complet avec les 3 phases du protocole (40+ endpoints)
- Signatures cryptographiques Ed25519 sur tous les bonds et messages
- Dashboard React temps réel (graphe de confiance, log d'activité, stats)
- Démo avec 4 agents autonomes LLM (Mercury 2) qui exécutent le protocole de bout en bout
- Démo scriptée (sans LLM) en backup

---

## 2. Scénarios d'Utilisation

### Scénario 1 — Le Handshake (Établir un partenariat)

> Acme Manufacturing et Beta Logistics travaillent déjà ensemble. Ils formalisent leur relation via PACT.

1. Acme s'enregistre sur le réseau avec son domaine, ses capacités (`manufacturing`, `industrial-parts`)
2. Acme propose un **bond** à Beta avec des termes (service, SLA, tarification, format de données)
3. Les deux signent cryptographiquement (Ed25519) — le bond devient actif
4. Acme initie une interaction `request_quote` sur leur bond
5. Échange structuré : demande de devis → réponse avec prix → acceptation/refus

### Scénario 2 — La Découverte (Trouver un nouveau partenaire)

> Acme a besoin d'un comptable mais ne connaît personne.

1. Acme diffuse une **intention** : "J'ai besoin de services comptables avec intégration EDI"
2. Le serveur matche les capacités de Gamma Accounting avec les besoins d'Acme
3. Gamma répond à l'intention avec une description de ses services
4. Ils établissent un bond (retour au scénario 1)

### Scénario 3 — Le Web of Trust (Recommandation pair-à-pair)

> Beta Logistics a aussi besoin d'un comptable, mais au lieu de diffuser, il interroge son réseau.

1. Beta interroge ses partenaires bondés : "Connaissez-vous un bon comptable ?"
2. Le serveur traverse le graphe : Beta → Acme (bondé) → Gamma (bondé, a la capacité comptable)
3. Beta reçoit une recommandation pour Gamma avec un score de confiance
4. Beta propose un bond à Gamma en citant la recommandation d'Acme

**Résultat :** Un triangle de confiance se forme organiquement, sans annuaire central.

---

## 3. Fonctions Réalisées

| Fonction | Statut | Description |
|----------|--------|-------------|
| Enregistrement d'agents | Fait | Inscription avec domaine, clé publique, capacités |
| Vérification d'identité | Fait | Vérification cryptographique de l'identité d'un agent |
| Bonds signés (Ed25519) | Fait | Proposition, signature et acceptation de partenariats |
| Templates d'interaction | Fait | `request_quote` (3 étapes), `place_order` (2 étapes) avec validation des champs |
| Broadcast d'intentions | Fait | Publication de besoins + matching automatique par capacités |
| Web of Trust | Fait | Requêtes pair-à-pair, recommandations via le graphe de confiance |
| Score de confiance | Fait | Calcul composite : bonds (15%/bond) + ancienneté (30%/an) + recommandations (10%/ref) |
| Dashboard temps réel | Fait | React 19, graphe circulaire, log d'activité, stats système |
| Agents autonomes LLM | Fait | 4 agents Mercury 2 avec function calling, exécution autonome du protocole |
| Démo scriptée | Fait | Démo complète sans LLM (backup) |

---

## 4. Planning — Polishing & Livrables

| # | Tâche | Date limite | Critères de validation | Risques | Plan B |
|---|-------|-------------|----------------------|---------|--------|
| 1 | Améliorations UX dashboard (animations, responsive) | 10 avril | Navigation fluide, affichage correct sur mobile et desktop | Temps frontend sous-estimé | Se concentrer uniquement sur le desktop |
| 2 | Ajout de templates additionnels (`status_update`, `dispute_resolution`) | 15 avril | Templates fonctionnels avec validation des champs à chaque étape | Design des étapes et champs requis | Se limiter à 1 seul template additionnel |
| 3 | Tests automatisés (unitaires + intégration) | 25 avril | Couverture des modules critiques (crypto, templates, trust scoring, endpoints) | Temps sous-estimé | Prioriser crypto et trust (fonctions critiques) |
| 4 | Documentation API complète | 01 mai | OpenAPI spec auto-générée depuis FastAPI + guide "Getting Started" | — | FastAPI génère déjà la doc automatiquement via `/docs` |
| 5 | Rendu écrit DVL (description prototype + questionnaire utilisateurs) | 15 mai | Document déposé sur DVL, questionnaire envoyé, ≥ 5 réponses | Taux de réponse faible | Solliciter directement des camarades |
| 6 | Améliorations post-questionnaire | 25 mai | Au moins 3 améliorations issues des retours utilisateurs implémentées | Retours hors scope | Prioriser les retours les plus fréquents |
| 7 | Polish démo showroom (scénario, narration, timing) | 29 mai | Démo de 5 min fluide, de bout en bout, sans intervention manuelle | Bug de dernière minute | Démo scriptée (`demo.py`) en backup de la démo IA |
| 8 | Rapport final | 04 juin | Rapport complet déposé sur DVL, comptes-rendus en annexe | Rédaction tardive | Commencer le squelette du rapport dès avril |

---

## 5. Jalons Clés

| Date | Jalon |
|------|-------|
| 20 mars | Réunion de suivi #1 (cette présentation) |
| ~10 avril | Réunion de suivi #2 |
| Début mai | Prototype finalisé (polish terminé) |
| Mi-mai | Rendu écrit DVL (description + questionnaire) |
| Fin mai | Réunion de suivi #3 (TD noté) |
| 4 juin | Showroom |
| Début juin | Rapport final sur DVL |

---

## 6. Stack Technique

| Composant | Technologie |
|-----------|------------|
| API Backend | Python 3.11+ / FastAPI / Uvicorn |
| Cryptographie | Ed25519 via PyNaCl (libsodium) |
| Agents IA | Mercury 2 (Inception Labs) via OpenAI SDK |
| Dashboard | React 19 + TypeScript + Vite 6 |
| Styling | CSS pur — esthétique brutalist/industrielle |
| HTTP Client | httpx (Python), fetch (browser) |
| Package Manager | uv (Python), npm (Node) |

---

*PACT : Parce que l'économie des agents a besoin de confiance, pas seulement de tokens.*
