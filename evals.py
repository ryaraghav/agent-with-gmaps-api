"""
Evals for the restaurant agent.

Usage:
    python evals.py                          # uses default model (gemini-2.0-flash)
    python evals.py --model gemini-1.5-pro   # compare a different model
"""
import argparse
import asyncio
import uuid
import os
import re
import json
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types, Client
from agent import prompts, tools
from app import render_html

load_dotenv()

# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------
TEST_CASES = [
    {
        "name": "basic_query",
        "query": "Find Italian restaurants in San Francisco",
        "criteria": (
            "User asked for Italian restaurants in San Francisco. "
            "Response should contain at least 3 Italian restaurants located in San Francisco."
        ),
    },
    {
        "name": "wheelchair_access",
        "query": "Find coffee shops in San Bruno with wheelchair access",
        "criteria": (
            "User specifically asked for wheelchair accessible coffee shops. "
            "Every restaurant recommended must have confirmed wheelchair access. "
            "Any restaurant showing wheelchair access as unavailable or unknown is a FAIL."
        ),
        "must_not_contain": ["Wheelchair Accessible Entrance: Not available"],
    },
    {
        "name": "no_location",
        "query": "Find me good Italian restaurants",
        "criteria": (
            "User did not provide a location. "
            "Response should ask the user for their location and NOT recommend specific restaurants."
        ),
    },
    {
        "name": "specific_time",
        "query": "Find restaurants in San Francisco open on Sunday at 8pm",
        "criteria": (
            "User asked for restaurants open on Sunday at 8pm. "
            "Only restaurants confirmed open on Sunday evening should be recommended. "
            "Any restaurant with unknown or missing hours should NOT be included."
        ),
    },
    {
        "name": "followup_with_quoted_context",
        "query": (
            "any with wheelchair access?\n\n"
            "---------- Forwarded message ---------\n"
            "Find coffee shops in San Bruno that serve breakfast"
        ),
        "criteria": (
            "This is a follow-up email. The previous context asked for coffee shops in San Bruno. "
            "Response should either: (a) recommend coffee shops in San Bruno with confirmed wheelchair access, "
            "OR (b) clearly state no matching restaurants were found. Both are acceptable outcomes. "
            "FAIL only if it recommends restaurants without confirmed wheelchair access."
        ),
        "must_not_contain": ["Wheelchair Accessible Entrance: Not available"],
    },
]

# ---------------------------------------------------------------------------
# Agent + runner setup
# ---------------------------------------------------------------------------
def setup_agent(model: str):
    agent = Agent(
        name="curator_agent",
        model=model,
        description="Help user find the best restaurants in a city",
        instruction=prompts.system_instruction_v8,
        tools=[tools.get_restaurants],
    )
    session_service = InMemorySessionService()
    runner = Runner(
        agent=agent,
        app_name="restaurant_agent_eval",
        session_service=session_service,
    )
    return runner, session_service


async def run_query(runner, session_service, query: str) -> str | None:
    session_id = str(uuid.uuid4())
    user_id = "eval_user"

    await session_service.create_session(
        app_name="restaurant_agent_eval",
        user_id=user_id,
        session_id=session_id,
    )

    content = types.Content(role="user", parts=[types.Part(text=query)])
    events = runner.run_async(user_id=user_id, session_id=session_id, new_message=content)

    raw = None
    async for event in events:
        if event.is_final_response():
            if event.content and event.content.parts:
                text_parts = [p.text for p in event.content.parts if hasattr(p, "text") and p.text]
                if text_parts:
                    raw = " ".join(text_parts)
            break

    if raw is None:
        return None

    # Mirror what app.py does: strip markdown wrappers, parse JSON, render HTML
    cleaned = re.sub(r'^```(?:json)?\s*', '', raw, flags=re.MULTILINE)
    cleaned = re.sub(r'\s*```$', '', cleaned, flags=re.MULTILINE).strip()
    # Normalize Python-style booleans/None the LLM sometimes outputs
    cleaned = re.sub(r'\bTrue\b', 'true', cleaned)
    cleaned = re.sub(r'\bFalse\b', 'false', cleaned)
    cleaned = re.sub(r'\bNone\b', 'null', cleaned)
    try:
        data = json.loads(cleaned)
        return render_html(data)
    except (json.JSONDecodeError, Exception):
        return cleaned  # fallback: return raw if not JSON


# ---------------------------------------------------------------------------
# Rule-based checks
# ---------------------------------------------------------------------------
def rule_checks(response: str | None, tc: dict) -> dict[str, bool]:
    results = {}

    results["non_empty"] = bool(response and len(response.strip()) > 100)
    results["valid_html"] = bool(response and "<html" in response.lower())
    results["no_description_placeholder"] = not bool(
        response and "Description not available" in response
    )
    results["no_hours_placeholder"] = not bool(
        response and "Hours: Not available" in response
    )

    for banned in tc.get("must_not_contain", []):
        key = f"not_contains:{banned[:30]}"
        results[key] = not bool(response and banned in response)

    return results


# ---------------------------------------------------------------------------
# LLM judge
# ---------------------------------------------------------------------------
def llm_judge(response: str | None, query: str, criteria: str) -> dict:
    if not response:
        return {"passed": False, "reason": "Empty response from agent"}

    client = Client(api_key=os.getenv("GOOGLE_API_KEY"))

    # Strip HTML tags so the judge sees plain text, not verbose markup
    plain = re.sub(r"<[^>]+>", " ", response)
    plain = re.sub(r"\s{2,}", " ", plain).strip()

    prompt = f"""You are strictly evaluating an AI restaurant recommendation agent.

User query:
{query}

Agent response (may be truncated):
{plain[:4000]}

Evaluation criteria:
{criteria}

Think step by step:
1. Does the response meet the criteria above? Explain briefly.
2. If any part of the response violates the criteria, explain what.

Then on the LAST line, write only: VERDICT: PASS or VERDICT: FAIL

Be strict. If any single restaurant in the response violates the criteria, it is a FAIL."""

    result = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt,
    )
    text = result.text.strip()
    last_line = text.splitlines()[-1].upper()
    passed = "VERDICT: PASS" in last_line
    reason_lines = [l for l in text.splitlines() if not l.upper().startswith("VERDICT")]
    reason = " ".join(reason_lines).strip()
    return {"passed": passed, "reason": reason}


# ---------------------------------------------------------------------------
# Main eval runner
# ---------------------------------------------------------------------------
async def run_evals(model: str, verbose: bool = False):
    print(f"\n{'='*60}")
    print(f"Model: {model}")
    print(f"{'='*60}\n")

    runner, session_service = setup_agent(model)
    results = []

    for tc in TEST_CASES:
        print(f"[ {tc['name']} ]")
        print(f"  Query: {tc['query'][:80]}...")

        response = await run_query(runner, session_service, tc["query"])

        if verbose:
            plain = re.sub(r"<[^>]+>", "", response or "").strip()
            plain = re.sub(r"\n{3,}", "\n\n", plain)
            print(f"\n  --- RESPONSE (plain text) ---\n{plain}\n  --- END ---\n")

        rules = rule_checks(response, tc)
        judge = llm_judge(response, tc["query"], tc["criteria"])

        rule_passed = all(rules.values())
        all_passed = rule_passed and judge["passed"]
        status = "PASS" if all_passed else "FAIL"

        print(f"  Status: {status}")

        if not rule_passed:
            for check, passed in rules.items():
                if not passed:
                    print(f"    FAIL rule  -> {check}")

        if not judge["passed"]:
            print(f"    FAIL judge -> {judge['reason']}")

        print()
        results.append({
            "test": tc["name"],
            "status": status,
            "rules": rules,
            "judge": judge,
            "response_length": len(response) if response else 0,
        })

    passed_count = sum(1 for r in results if r["status"] == "PASS")
    print(f"{'='*60}")
    print(f"Results: {passed_count}/{len(results)} passed  |  model: {model}")
    print(f"{'='*60}\n")
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model",
        default="gemini-2.0-flash",
        help="Gemini model to evaluate (e.g. gemini-2.0-flash, gemini-1.5-pro)",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Print full agent response for each test case",
    )
    args = parser.parse_args()
    asyncio.run(run_evals(args.model, verbose=args.verbose))
