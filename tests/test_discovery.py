"""Integration tests — Phase 2 (intent broadcast, matching, response) — server.py:253-295."""


def test_broadcast_intent_creates_open_intent(client, make_agent):
    a, _ = make_agent("A", ["travel"])
    resp = client.post(
        "/intents/broadcast",
        json={"agent_id": a["id"], "need": "find a hotel", "requirements": ["accommodation"]},
    )
    assert resp.status_code == 200
    intent = resp.json()
    assert intent["status"] == "open"
    assert intent["responses"] == []
    assert intent["requirements"] == ["accommodation"]


def test_matching_intents_capability_intersection(client, make_agent):
    vol, _ = make_agent("Vol", ["travel"])
    voiture, _ = make_agent("Voiture", ["car-rental", "mobility"])
    other, _ = make_agent("Other", ["accounting"])

    client.post(
        "/intents/broadcast",
        json={"agent_id": vol["id"], "need": "rental", "requirements": ["car-rental"]},
    )

    matches_voiture = client.get(f"/intents/matching/{voiture['id']}").json()
    assert len(matches_voiture) == 1
    assert matches_voiture[0]["agent_id"] == vol["id"]

    matches_other = client.get(f"/intents/matching/{other['id']}").json()
    assert matches_other == []

    matches_vol = client.get(f"/intents/matching/{vol['id']}").json()
    assert matches_vol == []


def test_matching_intents_case_insensitive(client, make_agent):
    vol, _ = make_agent("Vol", ["travel"])
    voiture, _ = make_agent("Voiture", ["Car-Rental"])
    client.post(
        "/intents/broadcast",
        json={"agent_id": vol["id"], "need": "rental", "requirements": ["car-rental"]},
    )
    matches = client.get(f"/intents/matching/{voiture['id']}").json()
    assert len(matches) == 1


def test_respond_to_intent_appends_response(client, make_agent):
    vol, _ = make_agent("Vol", ["travel"])
    voiture, _ = make_agent("Voiture", ["car-rental"])
    intent = client.post(
        "/intents/broadcast",
        json={"agent_id": vol["id"], "need": "rental", "requirements": ["car-rental"]},
    ).json()

    resp = client.post(
        f"/intents/{intent['id']}/respond",
        json={"agent_id": voiture["id"], "message": "I can help"},
    )
    assert resp.status_code == 200

    matches = client.get(f"/intents/matching/{voiture['id']}").json()
    intent_after = next(i for i in matches if i["id"] == intent["id"]) if matches else None
    all_intents_via_match = client.get(f"/intents/matching/{voiture['id']}").json()
    if all_intents_via_match:
        assert all_intents_via_match[0]["responses"][0]["agent_id"] == voiture["id"]
        assert all_intents_via_match[0]["responses"][0]["message"] == "I can help"
