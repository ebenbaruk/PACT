"""Integration tests — Phase 1 (handshake, bonds) — server.py:166-249."""

from pact.crypto import generate_keypair, sign


def test_register_agent_creates_id_and_logs(client):
    priv, pub = generate_keypair()
    resp = client.post(
        "/agents/register",
        json={"domain": "vol.test", "name": "Vol", "public_key": pub, "capabilities": ["travel"]},
    )
    assert resp.status_code == 200
    agent = resp.json()
    assert "id" in agent and len(agent["id"]) == 8
    assert agent["domain"] == "vol.test"
    assert agent["capabilities"] == ["travel"]
    assert agent["verified"] is False

    activity = client.get("/activity").json()
    assert any(e["type"] == "register" and e["source_id"] == agent["id"] for e in activity)


def test_get_agent_404_for_unknown(client):
    assert client.get("/agents/nope1234").status_code == 404


def test_verify_agent_flips_flag(client, make_agent):
    agent, _ = make_agent("A", ["x"])
    fresh = client.get(f"/agents/{agent['id']}").json()
    assert fresh["verified"] is True


def test_propose_bond_valid_signature(client, make_agent):
    a, a_priv = make_agent("A", ["travel"])
    b, _ = make_agent("B", ["accommodation"])

    terms = {"service": "travel-coordination", "sla": "24h"}
    sig = sign(str(sorted(terms.items())), a_priv)
    resp = client.post(
        "/bonds/propose",
        json={"proposer_id": a["id"], "accepter_id": b["id"], "terms": terms, "signature": sig},
    )
    assert resp.status_code == 200
    bond = resp.json()
    assert bond["status"] == "proposed"
    assert bond["signatures"]["proposer"] == sig


def test_propose_bond_rejects_bad_signature(client, make_agent):
    a, _ = make_agent("A", ["travel"])
    b, _ = make_agent("B", ["accommodation"])
    terms = {"service": "travel-coordination"}
    resp = client.post(
        "/bonds/propose",
        json={
            "proposer_id": a["id"],
            "accepter_id": b["id"],
            "terms": terms,
            "signature": "00" * 64,
        },
    )
    assert resp.status_code == 400
    assert "Invalid signature" in resp.json()["detail"]


def test_accept_bond_activates(client, make_agent, make_bond):
    a, a_priv = make_agent("A", ["travel"])
    b, b_priv = make_agent("B", ["accommodation"])
    bond = make_bond(a, a_priv, b, b_priv, {"service": "x"})
    assert bond["status"] == "active"
    assert "accepted_at" in bond
    assert "proposer" in bond["signatures"] and "accepter" in bond["signatures"]


def test_accept_bond_rejects_non_proposed(client, make_agent, make_bond):
    a, a_priv = make_agent("A", ["travel"])
    b, b_priv = make_agent("B", ["accommodation"])
    bond = make_bond(a, a_priv, b, b_priv, {"service": "x"})
    terms_str = str(sorted({"service": "x"}.items()))
    sig = sign(terms_str, b_priv)
    resp = client.post(f"/bonds/{bond['id']}/accept", json={"signature": sig})
    assert resp.status_code == 400
    assert "not in proposed state" in resp.json()["detail"]
