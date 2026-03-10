"""OpenAI tool definitions — one per PACT API endpoint."""

PACT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "register_agent",
            "description": "Register this agent on the PACT network",
            "parameters": {
                "type": "object",
                "properties": {
                    "domain": {"type": "string", "description": "The agent's domain (e.g. acme.com)"},
                    "name": {"type": "string", "description": "Display name of the agent"},
                    "capabilities": {"type": "array", "items": {"type": "string"}, "description": "List of capability tags"},
                },
                "required": ["domain", "name", "capabilities"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "verify_agent",
            "description": "Verify this agent's identity on the PACT network",
            "parameters": {
                "type": "object",
                "properties": {
                    "agent_id": {"type": "string", "description": "The agent ID to verify"},
                },
                "required": ["agent_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_agent_info",
            "description": "Get information about an agent by ID",
            "parameters": {
                "type": "object",
                "properties": {
                    "agent_id": {"type": "string", "description": "The agent ID to look up"},
                },
                "required": ["agent_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_trust_score",
            "description": "Get the trust score of an agent",
            "parameters": {
                "type": "object",
                "properties": {
                    "agent_id": {"type": "string", "description": "The agent ID"},
                },
                "required": ["agent_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "propose_bond",
            "description": "Propose a bond (partnership agreement) to another agent. Crypto signing is handled automatically.",
            "parameters": {
                "type": "object",
                "properties": {
                    "accepter_id": {"type": "string", "description": "The agent ID to propose the bond to"},
                    "terms": {"type": "object", "description": "Bond terms (e.g. service, sla, pricing, data_format)"},
                },
                "required": ["accepter_id", "terms"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "accept_bond",
            "description": "Accept a pending bond proposal. Crypto signing is handled automatically.",
            "parameters": {
                "type": "object",
                "properties": {
                    "bond_id": {"type": "string", "description": "The bond ID to accept"},
                },
                "required": ["bond_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_bonds",
            "description": "List all bonds in the system",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "broadcast_intent",
            "description": "Broadcast an intent describing what you need to find a partner",
            "parameters": {
                "type": "object",
                "properties": {
                    "need": {"type": "string", "description": "What you need (e.g. 'accounting services')"},
                    "requirements": {"type": "array", "items": {"type": "string"}, "description": "Required capability tags for matching"},
                },
                "required": ["need", "requirements"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_matching_intents",
            "description": "Check for open intents that match your capabilities",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "respond_to_intent",
            "description": "Respond to an open intent that matches your capabilities",
            "parameters": {
                "type": "object",
                "properties": {
                    "intent_id": {"type": "string", "description": "The intent ID to respond to"},
                    "message": {"type": "string", "description": "Your response message explaining how you can help"},
                },
                "required": ["intent_id", "message"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_network",
            "description": "Ask your bonded partners for recommendations for a specific need",
            "parameters": {
                "type": "object",
                "properties": {
                    "need": {"type": "string", "description": "What you're looking for (e.g. 'accounting')"},
                },
                "required": ["need"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_network",
            "description": "Get your trust network (bonded partners)",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_interactions",
            "description": "List all interactions in the system",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_interaction",
            "description": "Start a structured interaction (e.g. request_quote) on an active bond",
            "parameters": {
                "type": "object",
                "properties": {
                    "bond_id": {"type": "string", "description": "The bond ID to interact on"},
                    "template": {"type": "string", "enum": ["request_quote", "place_order"], "description": "Interaction template"},
                },
                "required": ["bond_id", "template"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "send_interaction_message",
            "description": "Send a message in an active interaction. Crypto signing is handled automatically. The data must include the required fields for the current step of the template.",
            "parameters": {
                "type": "object",
                "properties": {
                    "interaction_id": {"type": "string", "description": "The interaction ID"},
                    "data": {"type": "object", "description": "Message data with required fields for current step"},
                },
                "required": ["interaction_id", "data"],
            },
        },
    },
]
