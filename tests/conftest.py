"""Shared fixtures: reset in-memory state between tests, TestClient, agent helper."""

import pytest
from fastapi.testclient import TestClient

from pact import server
from pact.crypto import generate_keypair, sign


@pytest.fixture(autouse=True)
def reset_state():
    server.agents.clear()
    server.bonds.clear()
    server.interactions.clear()
    server.intents.clear()
    server.activity_log.clear()
    server._activity_idx = 0
    yield


@pytest.fixture
def client():
    return TestClient(server.app)


@pytest.fixture
def make_agent(client):
    def _make(name: str, capabilities: list[str], domain: str | None = None):
        priv, pub = generate_keypair()
        resp = client.post(
            "/agents/register",
            json={
                "domain": domain or f"{name.lower()}.test",
                "name": name,
                "public_key": pub,
                "capabilities": capabilities,
            },
        )
        assert resp.status_code == 200
        agent = resp.json()
        client.post(f"/agents/{agent['id']}/verify")
        return agent, priv

    return _make


@pytest.fixture
def make_bond(client):
    def _make(proposer: dict, proposer_priv: str, accepter: dict, accepter_priv: str, terms: dict):
        terms_str = str(sorted(terms.items()))
        prop_sig = sign(terms_str, proposer_priv)
        resp = client.post(
            "/bonds/propose",
            json={
                "proposer_id": proposer["id"],
                "accepter_id": accepter["id"],
                "terms": terms,
                "signature": prop_sig,
            },
        )
        assert resp.status_code == 200, resp.text
        bond = resp.json()
        acc_sig = sign(terms_str, accepter_priv)
        resp = client.post(f"/bonds/{bond['id']}/accept", json={"signature": acc_sig})
        assert resp.status_code == 200, resp.text
        return resp.json()

    return _make
