# PACT — Protocol for Agent Coordination & Trust

A lightweight coordination protocol that lets AI agents **discover**, **trust**, and **work together** through cryptographically signed bonds, capability-based discovery, and peer-referral trust networks.

PACT solves the "tourist vs. local" problem: today's AI agents operate as one-shot tourists — they complete a task and vanish. PACT turns them into locals who build lasting relationships, accumulate reputation, and coordinate through a web of trust.

---

## Architecture

```
src/pact/
├── server.py          ← FastAPI REST API (in-memory storage)
├── crypto.py          ← Ed25519 signing (PyNaCl)
├── templates.py       ← Structured interaction templates
└── ai/
    ├── agent.py       ← PACTAgent — LLM-powered autonomous agent
    └── tools.py       ← Tool definitions for LLM function calling

dashboard/             ← Live React dashboard (Vite + TypeScript)
├── src/
│   ├── App.tsx
│   ├── api.ts
│   ├── types.ts
│   ├── styles.css
│   ├── hooks/usePolling.ts
│   └── components/
│       ├── TopBar.tsx
│       ├── TrustNetwork.tsx
│       ├── ActivityLog.tsx
│       └── SystemInfo.tsx
└── vite.config.ts

ai_demo.py             ← AI demo — 4 autonomous agents, 3 acts
demo.py                ← Scripted demo — same flow, no LLM
```

---

## The Protocol — 3 Phases

### Phase 1: The Handshake

Two agents form a **bond** — a cryptographically signed partnership agreement with explicit terms.

1. Agent A registers on the network with its domain, name, public key, and capabilities
2. Agent A proposes a bond to Agent B with terms (service type, SLA, pricing, data format)
3. Both sides sign the terms with Ed25519 — the bond becomes active
4. Agents interact through **structured templates** (e.g., `request_quote`, `place_order`) where each step has required fields enforced by the server

### Phase 2: Discovery

Agents find new partners by broadcasting needs to the network.

1. Agent A broadcasts an **intent**: "I need accounting services with EDI integration"
2. The server matches intents against registered agent capabilities
3. Agent C (matching capabilities) discovers the intent and responds
4. If interested, they establish a bond (back to Phase 1)

### Phase 3: Web of Trust

Agents leverage existing bonds to find vetted partners through peer referrals.

1. Agent B needs accounting services but doesn't broadcast — it queries its **trust network**
2. The server traverses B's bonds, finds B's partner A, then finds A's partner C who has accounting capabilities
3. B receives a recommendation for C with trust score, referred by A
4. B proposes a bond to C, citing the referral

---

## Trust Model

Each agent's trust score is computed from three factors:

| Factor | Weight | Description |
|--------|--------|-------------|
| Bond count | 15% per bond | More active partnerships = higher trust |
| Referral count | 10% per referral | Being recommended by peers increases trust |
| Bond age | 30% over 1 year | Long-standing bonds signal reliability |

Score is capped at 1.0. New agents start at 0.0 — trust is earned, not given.

---

## Cryptography

All bond proposals, acceptances, and interaction messages are signed with **Ed25519** (via PyNaCl/libsodium):

- `generate_keypair()` — returns `(private_key_hex, public_key_hex)`
- `sign(message, private_key_hex)` — signs a message, returns hex signature
- `verify(message, signature_hex, public_key_hex)` — verifies a signature

The server rejects any bond or message with an invalid signature.

---

## Interaction Templates

Structured message flows that enforce required fields at each step:

**`request_quote`** — Request a price quote

| Step | Role | Required Fields |
|------|------|-----------------|
| 0 | Requester | `item`, `quantity` |
| 1 | Provider | `price`, `currency`, `valid_until` |
| 2 | Requester | `decision` |

**`place_order`** — Place an order

| Step | Role | Required Fields |
|------|------|-----------------|
| 0 | Requester | `item`, `quantity`, `delivery_date` |
| 1 | Provider | `order_id`, `estimated_delivery` |

---

## API Endpoints

### Dashboard

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/agents` | List all registered agents |
| GET | `/activity` | Last 50 activity events with details |
| GET | `/stats` | Agent count, bond count, avg trust |
| GET | `/interactions` | List all interactions |

### Phase 1: Handshake

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/agents/register` | Register a new agent |
| POST | `/agents/{id}/verify` | Verify agent identity |
| GET | `/agents/{id}` | Get agent details |
| GET | `/agents/{id}/trust` | Get trust score |
| POST | `/bonds/propose` | Propose a bond (signed) |
| POST | `/bonds/{id}/accept` | Accept a bond (signed) |
| GET | `/bonds` | List all bonds |
| GET | `/bonds/{id}` | Get bond details |

### Phase 2: Discovery

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/intents/broadcast` | Broadcast a need |
| GET | `/intents/matching/{id}` | Find intents matching agent capabilities |
| POST | `/intents/{id}/respond` | Respond to an intent |

### Phase 3: Web of Trust

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/network/query` | Query bonded partners for recommendations |
| GET | `/agents/{id}/network` | Get agent's bonded partners |

### Interactions

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/interactions/create` | Start a structured interaction on a bond |
| POST | `/interactions/{id}/message` | Send a signed message in an interaction |

---

## Setup

### Requirements

- Python >= 3.11
- [uv](https://docs.astral.sh/uv/) package manager
- Node.js >= 18 (for the dashboard)

### Install

```bash
# Clone the repo
git clone <repo-url> && cd PACT

# Install Python dependencies
uv sync

# Install dashboard dependencies
cd dashboard && npm install && cd ..
```

### Environment variables

Create a `.env` file at the project root:

```env
INCEPTION_API_KEY=your-inception-api-key   # Required for the AI demo (Mercury 2)
```

---

## Running

### 1. Start the server

```bash
uv run uvicorn src.pact.server:app
```

The API runs on `http://localhost:8000`. Interactive docs at `/docs`.

### 2. Start the dashboard

```bash
cd dashboard && npm run dev
```

Opens on `http://localhost:5173`. The dashboard polls the server every 2.5 seconds and displays:
- **Trust Network** — circular graph of agents with bracket-corner node boxes and animated dashed bond lines
- **Activity Log** — clickable event table with details (click a row to expand)
- **System Stats** — agent count, bond count, average trust score

### 3. Run a demo

**AI Demo** (autonomous LLM agents — recommended):

```bash
uv run python ai_demo.py
```

**Scripted Demo** (no LLM, direct API calls):

```bash
uv run python demo.py
```

---

## Demo Walkthrough

The demo tells the story of 4 business agents building a trust network from scratch. Each agent is backed by **Mercury 2** (Inception Labs) and makes autonomous decisions using PACT protocol tools.

### The Agents

| Agent | Domain | Capabilities | Role in the story |
|-------|--------|--------------|-------------------|
| Acme Manufacturing | acme.com | manufacturing, industrial-parts | Hub — initiates bonds and discovery |
| Beta Logistics | beta-logistics.com | shipping, cold-chain, logistics | Acme's shipping partner |
| Gamma Accounting | gamma-accounting.com | accounting, edi-integration, invoicing | Discovered via intent, then referred |
| Delta Supplies | delta-supplies.com | raw-materials, bulk-supply | Registers but stays isolated (trust = 0) |

### Setup — Agent Registration

All 4 agents register on the PACT network **in parallel**. Each agent:
1. Calls `register_agent` with its domain, name, and capabilities
2. Calls `verify_agent` to confirm its identity

### Act 1 — The Handshake (Phase 1)

Acme and Beta already work together — they formalize it on-chain:

1. **Acme proposes a bond** to Beta with shipping terms (`service=shipping`, `sla=48h`, `pricing=per-shipment`, `data_format=EDI`)
2. **Beta accepts** — the bond becomes active, both sides cryptographically signed
3. **Acme starts an interaction** — creates a `request_quote` on their bond
4. **Acme sends a quote request** — `item=Industrial Valves`, `quantity=500`
5. **Beta responds** with pricing — `price=2500.00`, `currency=USD`, `valid_until=2026-04-01`
6. **Acme accepts** the quote — `decision=accepted`, interaction completes

### Act 2 — Discovery (Phase 2)

Acme needs an accountant — instead of searching manually, it broadcasts to the network:

1. **Acme broadcasts an intent** — "I need accounting services" with requirements `['accounting', 'edi-integration']`
2. **Gamma checks for matching intents** — the server matches Gamma's capabilities against Acme's requirements
3. **Gamma responds** to the intent with a description of its services
4. **Acme proposes a bond** to Gamma with accounting terms (`service=accounting`, `scope`, `billing`, `data_format`)
5. **Gamma accepts** — second bond active

### Act 3 — Web of Trust (Phase 3)

Beta also needs accounting — but instead of broadcasting, it leverages its existing network:

1. **Beta queries its trust network** with `need=accounting`
2. The server traverses: Beta → Acme (bonded) → Gamma (bonded, has accounting capability)
3. **Beta receives a recommendation** for Gamma, referred by Acme, with trust score
4. **Beta proposes a bond** to Gamma, citing the referral
5. **Gamma accepts** — third bond active, triangle complete

### Finale — The Trust Network

```
Acme Manufacturing      trust=0.300  bonds=[Beta Logistics, Gamma Accounting]
Beta Logistics          trust=0.300  bonds=[Acme Manufacturing, Gamma Accounting]
Gamma Accounting        trust=0.300  bonds=[Acme Manufacturing, Beta Logistics]
Delta Supplies          trust=0.000  bonds=[none]
```

Three agents formed a fully connected trust triangle. Delta Supplies registered but never bonded — its trust score remains 0. Trust is earned through active participation, not mere presence.

---

## Tech Stack

| Component | Technology |
|-----------|------------|
| Server | FastAPI + Uvicorn |
| Crypto | Ed25519 via PyNaCl (libsodium) |
| AI Agents | Mercury 2 (Inception Labs) via OpenAI SDK |
| Dashboard | React 19 + TypeScript + Vite |
| Styling | Pure CSS — brutalist/industrial aesthetic |
| HTTP Client | httpx (Python), fetch (browser) |

---

## What PACT Is Not

- **Not a blockchain** — bonds are stored in-memory (PoC), not on a distributed ledger
- **Not an agent framework** — PACT is infrastructure that any agent framework can plug into
- **Not a marketplace** — PACT provides discovery and trust, not transaction processing
- **Not an identity provider** — domain-based identity is a starting point, not a full PKI

---

## License

MIT
