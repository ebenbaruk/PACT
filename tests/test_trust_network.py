"""Integration tests — Phase 3 (trust score, web of trust) — server.py:123-138, 299-344."""


def test_trust_score_zero_for_new_agent(client, make_agent):
    a, _ = make_agent("A", ["x"])
    resp = client.get(f"/agents/{a['id']}/trust").json()
    assert resp["trust_score"] == 0.0


def test_trust_score_increases_with_bonds(client, make_agent, make_bond):
    a, a_priv = make_agent("A", ["x"])
    b, b_priv = make_agent("B", ["y"])
    c, c_priv = make_agent("C", ["z"])
    make_bond(a, a_priv, b, b_priv, {"service": "ab"})
    make_bond(a, a_priv, c, c_priv, {"service": "ac"})

    score = client.get(f"/agents/{a['id']}/trust").json()["trust_score"]
    # 2 bonds * 0.15 = 0.30 (age ~0 so no age bonus, no referrals yet)
    assert score >= 0.30
    assert score < 0.35


def test_query_network_finds_friend_of_friend(client, make_agent, make_bond):
    notes, n_priv = make_agent("Notes", ["accounting"])
    vol, v_priv = make_agent("Vol", ["travel"])
    hotel, h_priv = make_agent("Hotel", ["hospitality", "accommodation"])

    make_bond(notes, n_priv, vol, v_priv, {"service": "audit"})
    make_bond(vol, v_priv, hotel, h_priv, {"service": "travel-coordination"})

    resp = client.post(
        "/network/query", json={"agent_id": notes["id"], "need": "hospitality"}
    )
    assert resp.status_code == 200
    recs = resp.json()
    assert len(recs) == 1
    rec = recs[0]
    assert rec["agent_id"] == hotel["id"]
    assert rec["referred_by"] == vol["id"]
    assert rec["referred_by_name"] == "Vol"
    assert "hospitality" in [c.lower() for c in rec["capabilities"]]


def test_get_network_lists_direct_partners(client, make_agent, make_bond):
    a, a_priv = make_agent("A", ["x"])
    b, b_priv = make_agent("B", ["y"])
    make_bond(a, a_priv, b, b_priv, {"service": "ab"})
    partners = client.get(f"/agents/{a['id']}/network").json()
    assert len(partners) == 1
    assert partners[0]["agent_id"] == b["id"]
    assert partners[0]["name"] == "B"
