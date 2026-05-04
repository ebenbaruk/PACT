"""Interaction templates — structured message flows between agents."""

TEMPLATES = {
    "request_quote": {
        "name": "request_quote",
        "description": "Request a price quote for goods or services",
        "steps": [
            {"role": "requester", "type": "quote_request", "required_fields": ["item", "quantity"]},
            {"role": "provider", "type": "quote_response", "required_fields": ["price", "currency", "valid_until"]},
            {"role": "requester", "type": "accept_reject", "required_fields": ["decision"]},
        ],
    },
    "place_order": {
        "name": "place_order",
        "description": "Place an order for goods or services",
        "steps": [
            {"role": "requester", "type": "order_request", "required_fields": ["item", "quantity", "delivery_date"]},
            {"role": "provider", "type": "order_confirmation", "required_fields": ["order_id", "estimated_delivery"]},
        ],
    },
    "request_booking": {
        "name": "request_booking",
        "description": "Request a booking (hotel, car rental, etc.) with dates and guests",
        "steps": [
            {"role": "requester", "type": "booking_request", "required_fields": ["item", "check_in", "check_out", "guests"]},
            {"role": "provider", "type": "booking_confirmation", "required_fields": ["booking_id", "total_price", "currency"]},
            {"role": "requester", "type": "accept_reject", "required_fields": ["decision"]},
        ],
    },
}


def validate_message(template_name: str, step_index: int, data: dict) -> str | None:
    """Validate a message against a template step. Returns error string or None."""
    template = TEMPLATES.get(template_name)
    if not template:
        return f"Unknown template: {template_name}"
    if step_index >= len(template["steps"]):
        return "Interaction already complete"
    step = template["steps"][step_index]
    missing = [f for f in step["required_fields"] if f not in data]
    if missing:
        return f"Missing required fields: {missing}"
    return None
