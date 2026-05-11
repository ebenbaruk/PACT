"""Integration tests — signed interactions on bonds — server.py:353-401."""

from pact.crypto import sign


def _signed_message(data: dict, priv: str) -> dict:
    return {"data": data, "signature": sign(str(sorted(data.items())), priv)}


def test_create_interaction_on_bond(client, make_agent, make_bond):
    a, a_priv = make_agent("A", ["x"])
    b, b_priv = make_agent("B", ["y"])
    bond = make_bond(a, a_priv, b, b_priv, {"service": "x"})

    resp = client.post(
        "/interactions/create",
        json={"bond_id": bond["id"], "template": "request_quote", "initiator_id": a["id"]},
    )
    assert resp.status_code == 200
    ix = resp.json()
    assert ix["status"] == "active"
    assert ix["current_step"] == 0
    assert ix["template"] == "request_quote"


def test_create_interaction_rejects_unknown_template(client, make_agent, make_bond):
    a, a_priv = make_agent("A", ["x"])
    b, b_priv = make_agent("B", ["y"])
    bond = make_bond(a, a_priv, b, b_priv, {"service": "x"})
    resp = client.post(
        "/interactions/create",
        json={"bond_id": bond["id"], "template": "nope", "initiator_id": a["id"]},
    )
    assert resp.status_code == 400


def test_send_message_advances_step(client, make_agent, make_bond):
    a, a_priv = make_agent("A", ["x"])
    b, b_priv = make_agent("B", ["y"])
    bond = make_bond(a, a_priv, b, b_priv, {"service": "x"})
    ix = client.post(
        "/interactions/create",
        json={"bond_id": bond["id"], "template": "request_quote", "initiator_id": a["id"]},
    ).json()

    msg = _signed_message({"item": "widget", "quantity": 5}, a_priv)
    resp = client.post(
        f"/interactions/{ix['id']}/message",
        json={"sender_id": a["id"], **msg},
    )
    assert resp.status_code == 200
    assert resp.json()["interaction_status"] == "active"

    interactions = client.get("/interactions").json()
    updated = next(i for i in interactions if i["id"] == ix["id"])
    assert updated["current_step"] == 1


def test_send_message_rejects_bad_signature(client, make_agent, make_bond):
    a, a_priv = make_agent("A", ["x"])
    b, b_priv = make_agent("B", ["y"])
    bond = make_bond(a, a_priv, b, b_priv, {"service": "x"})
    ix = client.post(
        "/interactions/create",
        json={"bond_id": bond["id"], "template": "request_quote", "initiator_id": a["id"]},
    ).json()

    resp = client.post(
        f"/interactions/{ix['id']}/message",
        json={
            "sender_id": a["id"],
            "data": {"item": "widget", "quantity": 5},
            "signature": "00" * 64,
        },
    )
    assert resp.status_code == 400
    assert "Invalid message signature" in resp.json()["detail"]


def test_send_message_rejects_missing_required_fields(client, make_agent, make_bond):
    a, a_priv = make_agent("A", ["x"])
    b, b_priv = make_agent("B", ["y"])
    bond = make_bond(a, a_priv, b, b_priv, {"service": "x"})
    ix = client.post(
        "/interactions/create",
        json={"bond_id": bond["id"], "template": "request_quote", "initiator_id": a["id"]},
    ).json()

    msg = _signed_message({"item": "widget"}, a_priv)  # missing 'quantity'
    resp = client.post(
        f"/interactions/{ix['id']}/message",
        json={"sender_id": a["id"], **msg},
    )
    assert resp.status_code == 400
    assert "Missing required fields" in resp.json()["detail"]


def test_send_message_completes_interaction(client, make_agent, make_bond):
    a, a_priv = make_agent("A", ["x"])
    b, b_priv = make_agent("B", ["y"])
    bond = make_bond(a, a_priv, b, b_priv, {"service": "x"})
    ix = client.post(
        "/interactions/create",
        json={"bond_id": bond["id"], "template": "request_quote", "initiator_id": a["id"]},
    ).json()

    step0 = _signed_message({"item": "widget", "quantity": 5}, a_priv)
    r0 = client.post(
        f"/interactions/{ix['id']}/message", json={"sender_id": a["id"], **step0}
    )
    assert r0.status_code == 200

    step1 = _signed_message(
        {"price": 100, "currency": "EUR", "valid_until": "2026-12-31"}, b_priv
    )
    r1 = client.post(
        f"/interactions/{ix['id']}/message", json={"sender_id": b["id"], **step1}
    )
    assert r1.status_code == 200

    step2 = _signed_message({"decision": "accepted"}, a_priv)
    r2 = client.post(
        f"/interactions/{ix['id']}/message", json={"sender_id": a["id"], **step2}
    )
    assert r2.status_code == 200
    assert r2.json()["interaction_status"] == "completed"
