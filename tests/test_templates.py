"""Unit tests for src/pact/templates.py — interaction template validation."""

from pact.templates import TEMPLATES, validate_message


def test_validate_unknown_template():
    err = validate_message("not_a_template", 0, {})
    assert err is not None
    assert "Unknown template" in err


def test_validate_missing_fields():
    err = validate_message(
        "request_booking", 0, {"item": "Hotel", "check_out": "2026-03-15", "guests": 1}
    )
    assert err is not None
    assert "check_in" in err
    assert "Missing required fields" in err


def test_validate_step_out_of_range():
    err = validate_message("place_order", 2, {})
    assert err == "Interaction already complete"


def test_validate_valid_message_each_template():
    samples = {
        "request_quote": [
            {"item": "X", "quantity": 1},
            {"price": 10, "currency": "EUR", "valid_until": "2026-12-31"},
            {"decision": "accepted"},
        ],
        "place_order": [
            {"item": "X", "quantity": 1, "delivery_date": "2026-04-01"},
            {"order_id": "ORD-1", "estimated_delivery": "2026-04-05"},
        ],
        "request_booking": [
            {"item": "Hotel", "check_in": "2026-03-12", "check_out": "2026-03-15", "guests": 1},
            {"booking_id": "B-1", "total_price": 450, "currency": "EUR"},
            {"decision": "accepted"},
        ],
    }
    for tpl_name, steps in samples.items():
        assert len(steps) == len(TEMPLATES[tpl_name]["steps"])
        for i, data in enumerate(steps):
            assert validate_message(tpl_name, i, data) is None, (tpl_name, i)
