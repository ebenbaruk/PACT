"""PACTAgent — an LLM-powered autonomous agent that uses the PACT protocol."""

import json
import os
import httpx
from openai import OpenAI

from ..crypto import generate_keypair, sign
from .tools import PACT_TOOLS

# Terminal colors
BOLD = "\033[1m"
DIM = "\033[2m"
CYAN = "\033[96m"
YELLOW = "\033[93m"
MAGENTA = "\033[95m"
RESET = "\033[0m"

AGENT_ICONS = {
    "Acme Manufacturing": "🏭",
    "Beta Logistics": "🚚",
    "Gamma Accounting": "📊",
    "Delta Supplies": "🔧",
}

MODEL = "mercury-2"


class PACTAgent:
    """An AI business agent backed by an LLM with PACT protocol tools."""

    def __init__(self, name: str, domain: str, persona: str, capabilities: list[str], base_url: str = "http://127.0.0.1:8000"):
        self.name = name
        self.domain = domain
        self.persona = persona
        self.capabilities = capabilities
        self.sk, self.pk = generate_keypair()
        self.agent_id: str | None = None
        self.icon = AGENT_ICONS.get(name, "🤖")
        self.openai = OpenAI(
            api_key=os.getenv("INCEPTION_API_KEY"),
            base_url="https://api.inceptionlabs.ai/v1",
        )
        self.http = httpx.Client(base_url=base_url, timeout=10)

    def _system_prompt(self) -> str:
        agent_id_line = f"\nYour agent_id: {self.agent_id}" if self.agent_id else ""
        return (
            f"You are {self.name}, an AI business agent for {self.domain}.\n"
            f"{self.persona}\n"
            f"Your capabilities: {self.capabilities}{agent_id_line}\n\n"
            f"You interact with other business agents through the PACT protocol.\n"
            f"Use the available tools to accomplish your goals.\n"
            f"When proposing bonds, keep terms SIMPLE — 3-5 short string key-value pairs max.\n"
            f"CRITICAL: Your final text reply MUST be ONE sentence. No lists, no bullet points, "
            f"no 'next steps'. Just say what you did in one sentence and stop."
        )

    def _sign_terms(self, terms: dict) -> str:
        return sign(str(sorted(terms.items())), self.sk)

    def _sign_data(self, data: dict) -> str:
        return sign(str(sorted(data.items())), self.sk)

    def _execute_tool(self, tool_name: str, args: dict) -> dict:
        """Execute a PACT tool call, handling crypto signing transparently."""
        try:
            if tool_name == "register_agent":
                r = self.http.post("/agents/register", json={
                    "domain": self.domain, "name": self.name,
                    "public_key": self.pk, "capabilities": self.capabilities,
                })
                result = r.json()
                if "id" in result:
                    self.agent_id = result["id"]
                return result

            elif tool_name == "verify_agent":
                return self.http.post(f"/agents/{args['agent_id']}/verify").json()

            elif tool_name == "get_agent_info":
                return self.http.get(f"/agents/{args['agent_id']}").json()

            elif tool_name == "get_trust_score":
                return self.http.get(f"/agents/{args['agent_id']}/trust").json()

            elif tool_name == "propose_bond":
                terms = args["terms"]
                return self.http.post("/bonds/propose", json={
                    "proposer_id": self.agent_id, "accepter_id": args["accepter_id"],
                    "terms": terms, "signature": self._sign_terms(terms),
                }).json()

            elif tool_name == "accept_bond":
                bond = self.http.get(f"/bonds/{args['bond_id']}").json()
                return self.http.post(f"/bonds/{args['bond_id']}/accept", json={
                    "signature": self._sign_terms(bond["terms"]),
                }).json()

            elif tool_name == "list_bonds":
                return self.http.get("/bonds").json()

            elif tool_name == "broadcast_intent":
                return self.http.post("/intents/broadcast", json={
                    "agent_id": self.agent_id,
                    "need": args["need"], "requirements": args.get("requirements", []),
                }).json()

            elif tool_name == "check_matching_intents":
                return self.http.get(f"/intents/matching/{self.agent_id}").json()

            elif tool_name == "respond_to_intent":
                return self.http.post(f"/intents/{args['intent_id']}/respond", json={
                    "agent_id": self.agent_id, "message": args["message"],
                }).json()

            elif tool_name == "query_network":
                return self.http.post("/network/query", json={
                    "agent_id": self.agent_id, "need": args["need"],
                }).json()

            elif tool_name == "get_network":
                return self.http.get(f"/agents/{self.agent_id}/network").json()

            elif tool_name == "list_interactions":
                return self.http.get("/interactions").json()

            elif tool_name == "create_interaction":
                return self.http.post("/interactions/create", json={
                    "bond_id": args["bond_id"], "template": args["template"],
                    "initiator_id": self.agent_id,
                }).json()

            elif tool_name == "send_interaction_message":
                data = args["data"]
                return self.http.post(f"/interactions/{args['interaction_id']}/message", json={
                    "sender_id": self.agent_id, "data": data,
                    "signature": self._sign_data(data),
                }).json()

            else:
                return {"error": f"Unknown tool: {tool_name}"}

        except httpx.HTTPStatusError as e:
            return {"error": str(e), "status_code": e.response.status_code}
        except Exception as e:
            return {"error": str(e)}

    def act(self, instruction: str) -> str:
        """Run an OpenAI tool-use loop until the LLM is done."""
        print(f"\n  {self.icon}  {YELLOW}{self.name}{RESET} is thinking...")
        print(f"     {DIM}Instruction: {instruction[:100]}{'...' if len(instruction) > 100 else ''}{RESET}")

        messages = [
            {"role": "system", "content": self._system_prompt()},
            {"role": "user", "content": instruction},
        ]

        for _ in range(5):
            response = self.openai.chat.completions.create(
                model=MODEL,
                messages=messages,
                tools=PACT_TOOLS,
                max_tokens=1000,
            )
            msg = response.choices[0].message

            if not msg.tool_calls:
                # Mercury 2 sometimes returns empty on first try — retry once
                if not msg.content:
                    continue
                print(f"     {CYAN}→ {msg.content}{RESET}")
                return msg.content

            messages.append(msg)
            for tc in msg.tool_calls:
                args = json.loads(tc.function.arguments)
                args_short = json.dumps(args, separators=(",", ":"))
                if len(args_short) > 80:
                    args_short = args_short[:77] + "..."
                print(f"     {MAGENTA}⚡ {tc.function.name}({args_short}){RESET}")

                result = self._execute_tool(tc.function.name, args)
                result_str = json.dumps(result, separators=(",", ":"))
                if len(result_str) > 100:
                    result_str = result_str[:97] + "..."
                print(f"     {DIM}   ← {result_str}{RESET}")

                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.id,
                    "content": json.dumps(result),
                })

        return "Max iterations reached"
