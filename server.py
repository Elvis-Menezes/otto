"""
Otto Bot Creator Server - Production Ready with MongoDB Persistence

This server uses MongoDB as Parlant's native backing store, ensuring:
- Agents persist across restarts (no rehydration needed)
- Guidelines and journeys persist automatically
- Sessions and events persist
- Single source of truth in MongoDB

Architecture:
┌──────────────────┐     ┌─────────────────────┐
│   Parlant SDK    │ ◄─► │      MongoDB        │
│   (server.py)    │     │   (backing store)   │
└──────────────────┘     └─────────────────────┘
         │
         ▼
┌──────────────────┐     ┌─────────────────────┐
│   API Server     │ ◄─► │    Web Frontend     │
│  (api_server.py) │     │   (web/app.js)      │
└──────────────────┘     └─────────────────────┘
"""
import asyncio
import json
import os
from typing import Any, Annotated

import httpx
import parlant.sdk as p
from dotenv import load_dotenv

# Import domain persistence layer (event-based, not Parlant internals)
from domain_persistence import initialize_persistence, get_persistence, shutdown_persistence
from domain_rehydration import rehydrate_bots_from_persistence, persist_bot_creation

load_dotenv()

# Server configuration
PARLANT_API_BASE_URL = os.getenv("PARLANT_API_BASE_URL", "http://localhost:8800")
PARLANT_API_TIMEOUT = int(os.getenv("PARLANT_API_TIMEOUT", "30"))
PARLANT_API_TOKEN = os.getenv("PARLANT_API_TOKEN")  # Optional bearer token

# MongoDB configuration (for domain persistence, NOT Parlant internal storage)
MONGODB_URI = os.getenv("MONGODB_URI", None)

REQUIRED_SPEC_FIELDS = {
    "name",
    "purpose",
    "scope",
    "target_users",
    "use_cases",
    "tone",
    "personality",
    "tools",
    "constraints",
    "guardrails",
    "guidelines",
    "journeys",
}
COMPOSITION_MODES = {
    "FLUID": p.CompositionMode.FLUID,
    "COMPOSITED": p.CompositionMode.COMPOSITED,
    "STRICT": p.CompositionMode.STRICT,
}


def _as_str_list(value: Any) -> list[str]:
    if isinstance(value, list) and all(isinstance(item, str) and item.strip() for item in value):
        return [item.strip() for item in value]
    return []


def _validate_guidelines(guidelines: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(guidelines, list) or not guidelines:
        return ["guidelines must be a non-empty list"]

    for index, guideline in enumerate(guidelines, start=1):
        if not isinstance(guideline, dict):
            errors.append(f"guidelines[{index}] must be an object")
            continue
        condition = guideline.get("condition")
        action = guideline.get("action")
        if not isinstance(condition, str) or not condition.strip():
            errors.append(f"guidelines[{index}].condition is required")
        if action is not None and (not isinstance(action, str) or not action.strip()):
            errors.append(f"guidelines[{index}].action must be a non-empty string when provided")
        criticality = guideline.get("criticality")
        if criticality is not None and criticality not in {"LOW", "MEDIUM", "HIGH"}:
            errors.append(f"guidelines[{index}].criticality must be LOW, MEDIUM, or HIGH")
    return errors


def _validate_journeys(journeys: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(journeys, list) or not journeys:
        return ["journeys must be a non-empty list"]

    for index, journey in enumerate(journeys, start=1):
        if not isinstance(journey, dict):
            errors.append(f"journeys[{index}] must be an object")
            continue
        title = journey.get("title")
        description = journey.get("description")
        conditions = journey.get("conditions")
        if not isinstance(title, str) or not title.strip():
            errors.append(f"journeys[{index}].title is required")
        if not isinstance(description, str) or not description.strip():
            errors.append(f"journeys[{index}].description is required")
        if not _as_str_list(conditions):
            errors.append(f"journeys[{index}].conditions must be a non-empty list of strings")
    return errors


def _validate_spec(spec: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    missing = REQUIRED_SPEC_FIELDS - spec.keys()
    if missing:
        errors.append(f"missing required fields: {', '.join(sorted(missing))}")

    for key in ("name", "purpose", "scope", "target_users", "tone", "personality"):
        value = spec.get(key)
        if value is None:
            continue
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{key} must be a non-empty string")

    if not _as_str_list(spec.get("use_cases")):
        errors.append("use_cases must be a non-empty list of strings")
    if not _as_str_list(spec.get("tools")):
        errors.append("tools must be a non-empty list of strings (use ['none'] if not needed)")
    if not _as_str_list(spec.get("constraints")):
        errors.append("constraints must be a non-empty list of strings")
    if not _as_str_list(spec.get("guardrails")):
        errors.append("guardrails must be a non-empty list of strings")

    errors.extend(_validate_guidelines(spec.get("guidelines")))
    errors.extend(_validate_journeys(spec.get("journeys")))

    composition_mode = spec.get("composition_mode")
    if composition_mode is not None and composition_mode not in COMPOSITION_MODES:
        errors.append("composition_mode must be one of FLUID, COMPOSITED, STRICT")

    max_iterations = spec.get("max_engine_iterations")
    if max_iterations is not None:
        if not isinstance(max_iterations, int) or max_iterations <= 0:
            errors.append("max_engine_iterations must be a positive integer")

    return errors


def _build_agent_description(spec: dict[str, Any]) -> str:
    tools = ", ".join(_as_str_list(spec.get("tools")))
    use_cases = "; ".join(_as_str_list(spec.get("use_cases")))
    constraints = "; ".join(_as_str_list(spec.get("constraints")))
    guardrails = "; ".join(_as_str_list(spec.get("guardrails")))

    return "\n".join(
        [
            f"Purpose: {spec['purpose']}",
            f"Scope: {spec['scope']}",
            f"Target users: {spec['target_users']}",
            f"Tone: {spec['tone']}",
            f"Personality: {spec['personality']}",
            f"Primary use cases: {use_cases}",
            f"Required tools/integrations: {tools}",
            f"Constraints: {constraints}",
            f"Guardrails: {guardrails}",
        ]
    )


async def _call_parlant_api(
    method: str,
    endpoint: str,
    data: dict[str, Any] | None = None,
) -> tuple[bool, dict[str, Any]]:
    url = f"{PARLANT_API_BASE_URL}{endpoint}"
    headers = {"Accept": "application/json", "Content-Type": "application/json"}
    if PARLANT_API_TOKEN:
        headers["Authorization"] = f"Bearer {PARLANT_API_TOKEN}"

    try:
        async with httpx.AsyncClient(timeout=PARLANT_API_TIMEOUT) as client:
            if method.upper() == "POST":
                response = await client.post(url, json=data, headers=headers)
            elif method.upper() == "GET":
                response = await client.get(url, headers=headers)
            else:
                return False, {"error": f"Unsupported HTTP method: {method}"}

            response.raise_for_status()
            return True, response.json()

    except httpx.TimeoutException:
        return False, {"error": f"API request timeout after {PARLANT_API_TIMEOUT}s"}
    except httpx.HTTPStatusError as exc:
        return False, {
            "error": f"API returned {exc.response.status_code}",
            "details": exc.response.text[:200],
        }
    except httpx.RequestError as exc:
        return False, {"error": f"API connection failed: {str(exc)}"}
    except Exception as exc:
        return False, {"error": f"Unexpected error: {str(exc)}"}


def _map_criticality_to_api(criticality: str | None) -> str:
    if criticality == "LOW":
        return "low"
    elif criticality == "HIGH":
        return "high"
    else:
        return "medium"


def _map_composition_mode_to_api(mode: str | None) -> str:
    if mode == "COMPOSITED":
        return "composited_canned"
    elif mode == "STRICT":
        return "strict_canned"
    else:
        return "fluid"


@p.tool
async def create_parlant_bot(
    context: p.ToolContext,
    spec_json: Annotated[
        str,
        p.ToolParameterOptions(
            description=(
                "Complete JSON bot specification with all required fields: name, purpose, scope, "
                "target_users, use_cases, tone, personality, tools, constraints, guardrails, "
                "guidelines, and journeys. Otto must construct this from gathered requirements."
            ),
            source="context",
            significance="Required to create a validated, production-ready Parlant bot via REST API",
            examples=[
                json.dumps({
                    "name": "Reva Support Bot",
                    "purpose": "E-commerce customer support for order tracking and returns",
                    "scope": "Order status, cancellations, refunds, returns, shipping info",
                    "target_users": "Existing customers with placed orders",
                    "use_cases": ["Track order", "Cancel order", "Request refund"],
                    "tone": "Friendly, empathetic, efficient",
                    "personality": "Helpful customer service rep",
                    "tools": ["none"],
                    "constraints": ["30-day cancellation policy", "No refunds over $500"],
                    "guardrails": ["Verify order number before actions"],
                    "guidelines": [
                        {
                            "condition": "Customer asks about order status",
                            "action": "Verify order number and provide tracking info",
                            "criticality": "HIGH"
                        }
                    ],
                    "journeys": [
                        {
                            "title": "Order Tracking",
                            "description": "Help customer find order status",
                            "conditions": ["When customer asks about delivery"]
                        }
                    ],
                    "composition_mode": "FLUID",
                    "max_engine_iterations": 3
                })
            ],
        ),
    ],
) -> p.ToolResult:
    try:
        spec = json.loads(spec_json)
    except json.JSONDecodeError as exc:
        return p.ToolResult({"status": "error", "errors": [f"Invalid JSON: {exc.msg}"]})

    if not isinstance(spec, dict):
        return p.ToolResult({"status": "error", "errors": ["Spec must be a JSON object"]})

    errors = _validate_spec(spec)
    if errors:
        return p.ToolResult({"status": "error", "errors": errors})

    agent_payload = {
        "name": spec["name"],
        "description": _build_agent_description(spec),
        "composition_mode": _map_composition_mode_to_api(spec.get("composition_mode")),
        "max_engine_iterations": spec.get("max_engine_iterations", 3),
    }

    success, agent_response = await _call_parlant_api("POST", "/agents", agent_payload)
    if not success:
        return p.ToolResult({
            "status": "error",
            "errors": [f"Failed to create agent: {agent_response.get('error')}"],
            "details": agent_response.get("details"),
        })

    agent_id = agent_response.get("id")
    agent_name = agent_response.get("name")
    agent_tag = f"agent:{agent_id}"

    created_guidelines = []
    for idx, guideline in enumerate(spec["guidelines"], 1):
        guideline_payload = {
            "condition": guideline["condition"],
            "action": guideline.get("action"),
            "description": guideline.get("description"),
            "criticality": _map_criticality_to_api(guideline.get("criticality")),
            "tags": [agent_tag],
        }

        success, guideline_response = await _call_parlant_api("POST", "/guidelines", guideline_payload)
        if success:
            created_guidelines.append({
                "id": guideline_response.get("id"),
                "condition": guideline["condition"]
            })
        else:
            created_guidelines.append({
                "error": f"Guideline {idx} failed: {guideline_response.get('error')}"
            })

    created_journeys = []
    for idx, journey in enumerate(spec["journeys"], 1):
        journey_payload = {
            "title": journey["title"],
            "description": journey["description"],
            "conditions": journey["conditions"],
            "tags": [agent_tag],
        }

        success, journey_response = await _call_parlant_api("POST", "/journeys", journey_payload)
        if success:
            created_journeys.append({
                "id": journey_response.get("id"),
                "title": journey["title"],
                "description": journey["description"],
                "conditions": journey["conditions"],
            })
        else:
            created_journeys.append({
                "error": f"Journey {idx} failed: {journey_response.get('error')}"
            })

    try:
        persistence = get_persistence()
        if persistence.enabled:
            guidelines_for_persistence = []
            for idx, guideline in enumerate(spec["guidelines"]):
                if idx < len(created_guidelines) and "id" in created_guidelines[idx]:
                    guidelines_for_persistence.append({
                        "id": created_guidelines[idx]["id"],
                        "condition": guideline["condition"],
                        "action": guideline.get("action"),
                        "description": guideline.get("description"),
                        "criticality": _map_criticality_to_api(guideline.get("criticality")),
                    })

            persisted = await persist_bot_creation(
                persistence=persistence,
                agent_id=agent_id,
                agent_name=agent_name,
                agent_description=_build_agent_description(spec),
                composition_mode=_map_composition_mode_to_api(spec.get("composition_mode")),
                max_engine_iterations=spec.get("max_engine_iterations", 3),
                guidelines=guidelines_for_persistence,
                journeys=created_journeys,
            )

            if persisted:
                print(f"💾 Persisted bot '{agent_name}' to MongoDB (ID: {agent_id})")
            else:
                print("⚠️  Bot created in Parlant but MongoDB persistence failed")
    except Exception as e:
        print(f"⚠️  MongoDB persistence error: {e}")

    return p.ToolResult(
        {
            "status": "created",
            "agent_id": agent_id,
            "agent_name": agent_name,
            "guidelines_created": len([g for g in created_guidelines if "id" in g]),
            "journeys_created": len([j for j in created_journeys if "id" in j]),
            "guidelines": created_guidelines,
            "journeys": created_journeys,
            "api_base_url": PARLANT_API_BASE_URL,
            "persisted_to_mongodb": persistence.enabled if 'persistence' in locals() else False,
        }
    )


async def _rehydrate_after_ready(server: p.Server, persistence: Any) -> None:
    await server.ready.wait()
    print("📥 Rehydrating bots from MongoDB...")
    try:
        rehydration_stats = await rehydrate_bots_from_persistence(server, persistence)
        if rehydration_stats.get("errors"):
            print(f"⚠️  {len(rehydration_stats['errors'])} error(s) during rehydration")
    except Exception as exc:
        print(f"⚠️  Failed to load bots from MongoDB: {exc}")


async def main():
    print("🚀 Starting Otto Bot Creator Server...")
    print(f"📡 Parlant API: {PARLANT_API_BASE_URL}")
    print(f"⏱️  API Timeout: {PARLANT_API_TIMEOUT}s")

    print("💾 Initializing domain persistence...")
    persistence_enabled, persistence_message = await initialize_persistence(MONGODB_URI)

    if persistence_enabled:
        print(f"✅ {persistence_message}")
        print("💾 Domain events will persist to MongoDB")
        print("🔄 Bots will be rehydrated on startup")
    else:
        print(f"⚠️  {persistence_message}")
        print("💾 Using in-memory only (no persistence)")
        print("💡 Set MONGODB_URI in .env to enable persistence")

    print("-" * 50)
    print("🏗️  Parlant: Using TransientDocumentDatabase (in-memory)")
    print("📦 Persistence: Event-based MongoDB mirroring (domain layer)")
    print("-" * 50)

    try:
        async with p.Server(nlp_service=p.NLPServices.openai) as server:
            agent = await server.create_agent(
                name="Otto",
                description=(
                    "Primary orchestrator for converting a business chatbot description into a fully "
                    "configured Parlant bot. Collect requirements, detect gaps, ask focused follow-ups, "
                    "produce a validated specification, and create the bot using Parlant REST APIs."
                ),
            )

            print(f"✅ Created Otto agent (ID: {agent.id})")

            await agent.create_guideline(
                condition="When a business user provides a bot description or asks to create a bot.",
                action=(
                    "Extract purpose, scope, target users, use cases, tone/personality, required tools, "
                    "constraints, and guardrails. Summarize extracted fields clearly before proceeding."
                ),
                description="Ensure requirements are captured explicitly from the start.",
                criticality=p.Criticality.HIGH,
            )

            await agent.create_guideline(
                condition="When any required parameter is missing, vague, or ambiguous.",
                action=(
                    "Ask ONE focused clarification question at a time and explain why that detail matters. "
                    "Guide the user step-by-step until all parameters are explicit and clear."
                ),
                description="Prevent assumptions and drive completion through structured questioning.",
                criticality=p.Criticality.HIGH,
            )

            await agent.create_guideline(
                condition="When preparing to build a bot specification from gathered requirements.",
                action=(
                    "Construct detailed Parlant guidelines and journeys that teach effective bot design, "
                    "enforce consistency, and apply safety/guardrails based on the user's requirements."
                ),
                description="Generate guidance and journeys from finalized requirements.",
                criticality=p.Criticality.MEDIUM,
            )

            await agent.create_guideline(
                condition="When all required parameters are explicit, validated, and confirmed by the user.",
                action=(
                    "Assemble a complete JSON bot specification with all required fields, validate it "
                    "against the schema, and call create_parlant_bot to instantiate the bot via REST API. "
                    "Provide the user with the created bot details including agent ID and confirmation."
                ),
                description="Only create bots from a fully validated specification using REST API.",
                criticality=p.Criticality.HIGH,
                tools=[create_parlant_bot],
            )

            await agent.create_journey(
                title="Bot Intake & Clarification",
                description="Gather requirements, close gaps, validate specification, and create bot via API.",
                conditions=[
                    "Start when the user describes a bot or requests a new bot.",
                    "Continue asking clarifying questions until all required parameters are explicit.",
                    "Validate the complete specification before calling the REST API.",
                ],
            )

            if persistence_enabled:
                persistence = get_persistence()
                asyncio.create_task(_rehydrate_after_ready(server, persistence))
            else:
                print("📭 MongoDB disabled - no bots to load")

            print("✅ Configuration complete. Server will start now.")

    finally:
        await shutdown_persistence()


asyncio.run(main())