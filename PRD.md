# PACT — Product Requirements Document

## Protocol for Agent Coordination & Trust

---

## 1. Vision

Every business will have an AI agent as its primary interface. Just as websites became the standard presence for businesses on the internet, AI agents will become the standard presence in the agent economy.

**The missing layer:** Today, AI agents can talk to humans — but they lack the infrastructure to discover, trust, and coordinate with each other in a structured, secure way. There is no "coordination stack" for B2B agent interactions.

**PACT** is that coordination stack. A lightweight API and SDK that enables AI agents to find partners, establish trusted long-term relationships, and coordinate through structured protocols — without marketplaces, without search engines, without platforms.

Think Stripe, not Amazon. Invisible infrastructure, not a destination.

## 2. Problem Statement

### The world without PACT

When Business A's agent needs to work with Business B's agent today, there is no standard way to:

1. **Discover** — How does Agent A find Agent B? There is no directory, no protocol, no standard identifier.
2. **Trust** — How does Agent A know it's really talking to Agent B and not a malicious impersonator? How does it know Agent B is reliable?
3. **Coordinate** — Once connected, how do they structure their interaction? Free-form conversation between AIs leads to hallucinations, misinterpretations, and errors.

### The Tourist vs. Local Problem

_(Inspired by [a16z's thesis](https://a16zcrypto.com/posts/article/against-b2b-payments-stablecoins/))_

Most current AI agent designs assume a **tourist** model: every interaction is a one-shot transaction. The agent searches, compares, negotiates from scratch — every single time.

But real B2B commerce works like **locals**: the butcher knows his suppliers, has pre-negotiated prices, established delivery schedules, and shared data formats. Trust is built over repeated interactions. New partners are found through referrals, not search engines.

**PACT enables agents to transition from tourists to locals** — and to stay locals.

## 3. Target Users

| Persona | Description |
|---------|-------------|
| **Agent Developers** | Engineers building AI agents for businesses. They integrate the PACT SDK into their agents to enable B2B interactions. |
| **Businesses with AI Agents** | Companies that have deployed (or are deploying) AI agents and need them to interact with agents from other companies or clients. |
| **Platform Builders** | Teams building agent orchestration platforms who need a trust and coordination layer between agents from different organizations. |

## 4. Core Primitives

PACT is built on three simple primitives. Everything else flows from these.

### 4.1 BroadcastIntent()

**Purpose:** Find a new partner when you don't have one yet (the "tourist moment").

**How it works:** An agent publishes a structured intent describing what it needs. Only agents whose capabilities match — and who meet a minimum trust threshold — can intercept and respond.

**Key point:** This is not a marketplace listing. It's a one-time signal to find a long-term partner, not to make a one-off purchase.

```
BroadcastIntent({
  need: "logistics_provider",
  requirements: {
    capabilities: ["cold_chain", "eu_delivery"],
    volume: "500_units_monthly",
    data_formats: ["edi_x12", "json_api"]
  },
  relationship_type: "long_term",
  trust_minimum: 0.7
})
```

**User Stories:**
- As a business agent, I can describe what kind of partner I need so that matching agents can find me.
- As a receiving agent, I only see intents that match my declared capabilities, so I'm not flooded with irrelevant requests.
- As either party, I can see the trust score of the other agent before engaging, so I can filter out unknown or low-trust entities.

---

### 4.2 EstablishLocalBond()

**Purpose:** Seal a relationship. Turn a first interaction into a long-term partnership with pre-negotiated terms.

**How it works:** After a successful first interaction (or negotiation), both agents sign a "bond" — a structured agreement that defines how they will interact going forward. This includes data formats, pricing terms, communication protocols, SLAs, and escalation rules.

Once a bond exists, future interactions are **instant and frictionless**. No re-negotiation. No re-discovery. Just execution.

```
EstablishLocalBond({
  partner: "agent://acme-logistics.com",
  terms: {
    pricing: { model: "volume_discount", rates: [...] },
    data_format: "edi_x12",
    sla: { response_time: "30s", uptime: "99.9%" },
    escalation: "human_review_above_10k"
  },
  duration: "12_months",
  auto_renew: true
})
```

**User Stories:**
- As a business agent, I can formalize a relationship with a partner agent so that all future interactions follow agreed-upon terms.
- As either agent, I can execute transactions instantly with a bonded partner without re-negotiating terms each time.
- As a business owner, I can review and approve bonds before they are signed, maintaining human oversight on partnerships.

---

### 4.3 QueryLocalNetwork()

**Purpose:** Find new partners through trusted referrals — algorithmic word-of-mouth.

**How it works:** Instead of broadcasting to the world, an agent asks its existing bonded partners: "Do you know a good accountant?" The partner checks its own bonds and returns recommendations with trust attestations.

This is how the trust graph grows organically. No central authority ranks agents. Trust propagates through the network, like a village where the baker recommends the butcher.

```
QueryLocalNetwork({
  need: "accounting_service",
  ask: ["agent://my-logistics-partner.com", "agent://my-supplier.com"],
  min_trust: 0.6,
  max_hops: 2
})
```

**User Stories:**
- As a business agent, I can ask my trusted partners for recommendations so I find reliable new partners faster.
- As a recommending agent, I can vouch for partners I've worked with, sharing my trust attestation.
- As a receiving agent, I get recommendations pre-filtered by trust level, so discovery is efficient and safe.

---

## 5. Trust & Identity

### Identity

Simple, domain-based identity. An agent's identity is tied to its organization's domain, verified through standard TLS/SSL certificates.

- Agent identity: `agent://company-domain.com`
- Verification: cryptographic proof that the agent is authorized by the domain owner
- No proprietary identity system. Leverage existing internet infrastructure.

### Trust Score

Trust is computed from three signals:

1. **Bond history** — How many successful bonds does this agent have? How long have they lasted?
2. **Peer attestations** — How many agents in the network vouch for this agent?
3. **Transaction track record** — Ratio of successful vs. failed/disputed interactions.

Trust is **contextual**: an agent can be highly trusted for logistics but unknown for accounting. Trust scores are scoped to capability domains.

### Guardrails

PACT enforces interaction guardrails to prevent agent-to-agent manipulation:

- Structured message formats (no free-form prompt injection)
- Interaction scoped to declared capabilities
- Human escalation triggers for high-value decisions

## 6. Coordination Protocol

When two agents interact through PACT, they don't have free-form conversations. They enter **structured negotiation spaces**.

### Interaction Templates

PACT provides a library of standard interaction templates:

| Template | Description |
|----------|-------------|
| `request_quote` | Request and receive a structured price quote |
| `place_order` | Submit a structured order with all required fields |
| `schedule_meeting` | Negotiate and confirm a time slot |
| `request_proposal` | Request a detailed proposal for a service |
| `status_update` | Exchange structured status updates on ongoing work |
| `dispute_resolution` | Structured escalation and resolution flow |

Templates are extensible. Businesses can define custom templates for their specific workflows and share them with bonded partners.

### Interaction Flow

```
1. Agent A initiates interaction using a template
2. PACT verifies both identities
3. PACT creates an ephemeral interaction space
4. Agents exchange structured messages within the template
5. On agreement, PACT records the outcome
6. Both agents receive a signed receipt
```

## 7. MVP Scope

### Phase 1: The Handshake (MVP)

Build the minimum to enable two agents to discover, verify, and establish a trusted bond.

**In scope:**
- Agent identity registration (domain-based)
- Identity verification endpoint
- `EstablishLocalBond()` — create, sign, and store bonds between two agents
- Basic interaction templates (`request_quote`, `place_order`)
- Simple trust score (bond count + duration)
- REST API + Python SDK

**Out of scope for MVP:**
- `BroadcastIntent()` (Phase 2)
- `QueryLocalNetwork()` (Phase 3)
- Custom interaction templates
- Multi-agent negotiations (3+ parties)
- Payment processing
- Agent hosting or deployment
- UI dashboard (API-first)

### Phase 2: Discovery

- `BroadcastIntent()` — publish/subscribe intent matching
- Intent filtering by capability and trust threshold
- Notification system for matching intents

### Phase 3: Web of Trust

- `QueryLocalNetwork()` — peer referral queries
- Trust graph computation across bonds
- Multi-hop trust propagation (friend of a friend)
- Trust decay over time for inactive bonds

## 8. Technical Approach

### Principles
- **Simple over clever.** Standard REST API. No blockchain. No complex distributed systems. No exotic protocols.
- **API-first.** Everything is an API call. The SDK is a thin wrapper.
- **Stateless service.** PACT is a coordination layer, not a data warehouse. Agents own their data.

### Stack (v1)
- **API:** REST (JSON) with OpenAPI spec
- **SDK:** Python first, TypeScript second
- **Identity:** Domain verification via DNS TXT records + TLS certificate validation
- **Storage:** PostgreSQL for bonds, trust scores, and interaction receipts
- **Crypto:** Standard asymmetric key signing (Ed25519) for bond signatures and message authentication
- **Hosting:** Single-region cloud deployment (keep it simple)

### API Surface (MVP)

```
POST   /agents/register          — Register an agent identity
GET    /agents/{id}/verify       — Verify an agent's identity
POST   /bonds/propose            — Propose a bond to another agent
POST   /bonds/{id}/accept        — Accept a bond proposal
GET    /bonds/{id}               — Get bond details and terms
POST   /interactions/create      — Start a structured interaction
POST   /interactions/{id}/message — Send a message within an interaction
GET    /agents/{id}/trust        — Get an agent's trust score
```

## 9. Success Metrics

| Metric | Target (6 months) |
|--------|-------------------|
| Registered agents | 100+ |
| Active bonds | 50+ |
| Successful interactions through bonds | 500+ |
| SDK downloads | 1,000+ |
| Average bond duration | > 30 days |
| Interaction success rate | > 95% |

## 10. What PACT is NOT

- **Not a marketplace.** Agents don't browse listings. They find partners through intents and referrals.
- **Not a search engine.** PACT doesn't crawl or index. Discovery is intent-driven and trust-driven.
- **Not a social network.** No profiles, no feeds, no followers. Just bonds and interactions.
- **Not an agent hosting platform.** PACT doesn't run agents. It connects them.
- **Not a payment system.** PACT coordinates business interactions. Payment rails are separate.

---

_PACT: Because the agent economy needs trust, not just tokens._
