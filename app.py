from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv
from agent.agent import root_agent
from google.adk import Runner
from google.adk.sessions import VertexAiSessionService, InMemorySessionService
from google.genai import types
import os
import uuid
import logging
import re
import json

# Structured JSON logging for Cloud Run / Cloud Logging
logging.basicConfig(level=logging.WARNING)  # suppress noisy library DEBUG output

def _log(severity: str, message: str, **kwargs):
    """Emit a structured JSON log entry that Cloud Logging can parse and filter."""
    entry = {"severity": severity, "message": message}
    entry.update(kwargs)
    print(json.dumps(entry), flush=True)

load_dotenv()


def _is_placeholder(s: str) -> bool:
    """Return True if a string is a known placeholder that should not be rendered."""
    low = s.lower().strip()
    return "not available" in low or low == "n/a" or low == ""


def render_html(data: dict) -> str:
    """Convert structured restaurant JSON from the agent into a styled HTML email."""
    message = data.get("message", "Here are your restaurant recommendations.")
    restaurants = data.get("restaurants", [])

    FEATURE_LABELS = {
        "reservable": "Reservations",
        "wheelchair_accessible": "Wheelchair Accessible",
        "serves_breakfast": "Breakfast",
        "serves_lunch": "Lunch",
        "serves_dinner": "Dinner",
        "serves_brunch": "Brunch",
        "serves_vegetarian_food": "Vegetarian",
        "serves_wine": "Wine",
        "serves_beer": "Beer",
        "takeout": "Takeout",
    }

    cards = ""
    for r in restaurants:
        name = r.get("name", "")
        address = r.get("address", "")
        rating = r.get("rating")
        if isinstance(rating, str) and _is_placeholder(rating):
            rating = None
        description = r.get("description", "")
        if isinstance(description, str) and _is_placeholder(description):
            description = ""
        hours = [h for h in r.get("hours", []) if not (isinstance(h, str) and _is_placeholder(h))]
        website = r.get("website", "")
        features = {k: v for k, v in r.get("features", {}).items() if v is True}
        review_highlights = r.get("review_highlights", [])

        rating_html = (
            f'<p style="margin:5px 0;color:#ee5a6f;font-weight:600;">{rating}/5</p>'
            if rating else ""
        )
        address_html = (
            f'<p style="margin:5px 0;color:#636e72;font-size:14px;">{address}</p>'
            if address else ""
        )
        description_html = (
            f'<p style="margin:10px 0;font-style:italic;opacity:0.9;">{description}</p>'
            if description else ""
        )
        hours_html = (
            f'<p style="margin:5px 0;font-size:13px;color:#636e72;"><strong>Hours:</strong> {", ".join(hours)}</p>'
            if hours else ""
        )
        website_html = (
            f'<p style="margin:5px 0;"><a href="{website}" style="color:#ee5a6f;text-decoration:none;font-size:13px;">Visit Website</a></p>'
            if website else ""
        )
        badges = "".join(
            f'<span style="background:#ffe5d9;border-radius:20px;padding:4px 12px;font-size:12px;margin-right:6px;margin-bottom:4px;display:inline-block;">{FEATURE_LABELS.get(k, k)}</span>'
            for k in features
        )
        badges_html = f'<div style="margin-top:10px;">{badges}</div>' if badges else ""
        highlights_html = (
            '<div style="margin-top:12px;padding:10px 14px;background:#f9f4f4;border-radius:8px;">'
            '<p style="margin:0 0 6px 0;font-size:12px;color:#636e72;font-weight:600;letter-spacing:0.5px;">WHAT PEOPLE SAY</p>'
            + "".join(
                f'<p style="margin:4px 0;font-size:13px;color:#2d3436;font-style:italic;">&ldquo;{h}&rdquo;</p>'
                for h in review_highlights
            )
            + "</div>"
        ) if review_highlights else ""

        cards += f"""
        <div style="background:#fff;border-radius:12px;padding:25px;margin-bottom:20px;box-shadow:0 2px 8px rgba(0,0,0,0.08);">
          <h3 style="margin:0 0 8px 0;font-size:22px;font-weight:500;color:#ee5a6f;">{name}</h3>
          {rating_html}{address_html}{description_html}{hours_html}{website_html}{badges_html}{highlights_html}
        </div>"""

    return f"""<html>
<body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','Helvetica Neue',Arial,sans-serif;background:#fafafa;padding:20px;color:#2d3436;max-width:620px;margin:0 auto;">
  <h2 style="font-size:28px;font-weight:300;letter-spacing:1.5px;color:#ee5a6f;border-bottom:2px solid #ffe5d9;padding-bottom:12px;">AI Concierge recommends</h2>
  <p style="font-size:15px;line-height:1.8;margin-bottom:24px;">{message}</p>
  {cards}
  <p style="margin-top:30px;padding-top:20px;border-top:1px solid #ffe5d9;color:#636e72;font-size:13px;">Reply to this email if you have any follow-up questions.</p>
</body>
</html>"""


# This tells the FastAPI app what the request body POST request (JSON) should look like
class Req(BaseModel):
    query: str
    from_: str | None = None
    session_id: str | None = None  # Optional session ID for conversation continuity
    user_id: str | None = None  # Optional user ID

app = FastAPI()

# Initialize ADK Runner with session service (VertexAI or InMemory fallback)
# Get configuration from environment variables
PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT_ID", "")
LOCATION = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
AGENT_ENGINE_ID = os.getenv("AGENT_ENGINE_ID", "")

# Create session service and runner
session_service = None
runner = None

# Try to use VertexAiSessionService first (for persistent sessions)
if PROJECT_ID and AGENT_ENGINE_ID:
    try:
        session_service = VertexAiSessionService(
            PROJECT_ID,
            LOCATION,
            AGENT_ENGINE_ID
        )
        print("✅ Using VertexAiSessionService (persistent sessions)")
        print(f"   Project: {PROJECT_ID}, Location: {LOCATION}, Engine: {AGENT_ENGINE_ID}")
    except Exception as e:
        print(f"⚠️  Could not initialize VertexAiSessionService: {e}")
        print("   Falling back to InMemorySessionService")

# Fall back to InMemorySessionService if VertexAI not available
if session_service is None:
    try:
        session_service = InMemorySessionService()
        print("✅ Using InMemorySessionService (sessions in memory only)")
        print("   Note: Sessions won't persist across server restarts")
    except Exception as e:
        print(f"❌ Could not initialize session service: {e}")

# Create runner with session service
if session_service:
    try:
        runner = Runner(
            agent=root_agent,
            app_name="restaurant_agent_app",
            session_service=session_service
        )
        print("✅ ADK Runner initialized successfully")
    except Exception as e:
        print(f"❌ Could not initialize Runner: {e}")

@app.post("/run")
async def run(req: Req):
    """
    Get conversational restaurant recommendations using the agent.
    Returns natural language response with restaurant details.
    
    For follow-up questions, include the session_id from the previous response
    to maintain conversation context. The agent will have access to all previous
    messages in the session.
    
    Example:
    - First request: {"query": "Italian restaurants in San Francisco"}
    - Follow-up: {"query": "What are their hours?", "session_id": "<from previous response>"}
    """
    try:
        # Ensure runner is initialized
        if runner is None:
            return {
                "error": "Agent runner not initialized. Please check server logs for initialization errors."
            }
        
        # Format the query for the agent
        query = req.query.strip()
        if req.from_:
            query = f"{query} in {req.from_}"

        _log("INFO", "request_received", query_preview=query[:300], from_=req.from_)
        
        # Handle session_id based on session service type
        user_id = req.user_id or "default_user"
        
        # For VertexAI: session_id must be created by VertexAI API, not a UUID
        # For InMemory: we can use UUIDs and create sessions manually
        from google.adk.sessions import VertexAiSessionService
        
        if isinstance(session_service, VertexAiSessionService):
            # For VertexAI, sessions must be created through VertexAI API
            # If session_id is provided, verify it exists
            # If not provided, create a new session through VertexAI API
            if req.session_id:
                session_id = req.session_id
                # Verify session exists
                try:
                    existing_session = await session_service.get_session(
                        app_name="restaurant_agent_app",
                        user_id=user_id,
                        session_id=session_id
                    )
                    if existing_session is None:
                        return {
                            "error": f"Session {session_id} not found in VertexAI. Please create a new session or use a valid session ID."
                        }
                except Exception as e:
                    return {
                        "error": f"Invalid session ID for VertexAI: {str(e)}"
                    }
            else:
                # Create a new session through VertexAI API
                try:
                    new_session = await session_service.create_session(
                        app_name="restaurant_agent_app",
                        user_id=user_id
                    )
                    session_id = new_session.id
                except Exception as e:
                    return {
                        "error": f"Failed to create VertexAI session: {str(e)}"
                    }
        elif isinstance(session_service, InMemorySessionService):
            # For InMemory, generate UUID if not provided
            session_id = req.session_id or str(uuid.uuid4())
            
            # Create session if it doesn't exist (required before use)
            # get_session returns None if session doesn't exist (doesn't raise exception)
            existing_session = await session_service.get_session(
                app_name="restaurant_agent_app",
                user_id=user_id,
                session_id=session_id
            )
            if existing_session is None:
                # Session doesn't exist, create it
                await session_service.create_session(
                    app_name="restaurant_agent_app",
                    user_id=user_id,
                    session_id=session_id
                )
        else:
            # Fallback: generate session_id
            session_id = req.session_id or str(uuid.uuid4())
        
        # Create message content
        content = types.Content(role='user', parts=[types.Part(text=query)])
        
        # Run the agent using the runner (async)
        # The runner automatically maintains conversation history in the session
        # When the same session_id is used, it has access to all previous messages
        events = runner.run_async(
            user_id=user_id,
            session_id=session_id,
            new_message=content
        )
        
        # Extract final response from events and ensure session persists
        final_response = None
        actual_session_id = session_id
        
        async for event in events:
            # Try to capture session_id from events if it was auto-generated
            if actual_session_id is None and hasattr(event, 'session_id'):
                actual_session_id = event.session_id
            elif actual_session_id is None and hasattr(event, 'session') and hasattr(event.session, 'id'):
                actual_session_id = event.session.id
            
            if event.is_final_response():
                # Check if event.content exists and has parts
                if event.content and hasattr(event.content, 'parts') and event.content.parts:
                    # Get text from all parts
                    text_parts = [part.text for part in event.content.parts if hasattr(part, 'text') and part.text]
                    if text_parts:
                        final_response = ' '.join(text_parts)
                        _log("INFO", "agent_response_received", response_length=len(final_response), response_preview=final_response[:300])
                    else:
                        _log("WARNING", "agent_final_event_empty_parts")
                else:
                    _log("WARNING", "agent_final_event_no_content")
                break
        
        # Ensure session is properly maintained for follow-up questions
        # The ADK Runner automatically appends messages to the session, but we should verify
        # For InMemorySessionService, verify the session has the conversation history
        if isinstance(session_service, InMemorySessionService):
            try:
                # Get the session to verify it exists and has events
                session = await session_service.get_session(
                    app_name="restaurant_agent_app",
                    user_id=user_id,
                    session_id=actual_session_id
                )
                if session:
                    # Session exists and should have conversation history
                    # The runner automatically appends messages to the session
                    pass
            except Exception:
                # Session retrieval failed, but this shouldn't break the response
                pass
        
        if final_response:
            # Strip markdown code blocks if present
            cleaned = re.sub(r'^```(?:json)?\s*', '', final_response, flags=re.MULTILINE)
            cleaned = re.sub(r'\s*```$', '', cleaned, flags=re.MULTILINE)
            cleaned = cleaned.strip()

            # Normalize Python-style booleans/None the LLM sometimes outputs
            cleaned = re.sub(r'\bTrue\b', 'true', cleaned)
            cleaned = re.sub(r'\bFalse\b', 'false', cleaned)
            cleaned = re.sub(r'\bNone\b', 'null', cleaned)

            # Try to parse as JSON and render HTML
            try:
                data = json.loads(cleaned)
                restaurant_count = len(data.get("restaurants", []))
                _log("INFO", "json_parse_success", restaurant_count=restaurant_count, message=data.get("message", "")[:200])
                html_response = render_html(data)
            except (json.JSONDecodeError, Exception) as parse_err:
                _log("ERROR", "json_parse_failed", error=str(parse_err), response_preview=cleaned[:300])
                html_response = cleaned

            return {
                "response": html_response,
                "session_id": actual_session_id,
                "message": "Use this session_id in your next request to continue the conversation" if req.session_id is None else None
            }
        else:
            _log("ERROR", "no_final_response", query_preview=query[:300])
            return {
                "response": "I received your query but couldn't generate a response.",
                "session_id": actual_session_id
            }

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        _log("ERROR", "unhandled_exception", error=str(e), traceback=error_details[:1000])
        return {"error": f"Internal server error: {str(e)}", "details": error_details}

@app.post("/agent-response")
async def agent_response(req: Req):
    """
    Alias for /run endpoint - same functionality.
    Returns conversational agent response.
    """
    return await run(req)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)