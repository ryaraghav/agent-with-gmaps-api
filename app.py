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

# Enable DEBUG logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)

load_dotenv()

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
            # Strip markdown code blocks if present (agent sometimes wraps HTML in ```html blocks)
            # Remove ```html or ``` at the start and ``` at the end
            cleaned_response = re.sub(r'^```html?\s*', '', final_response, flags=re.MULTILINE)
            cleaned_response = re.sub(r'^```\s*', '', cleaned_response, flags=re.MULTILINE)
            cleaned_response = re.sub(r'\s*```$', '', cleaned_response, flags=re.MULTILINE)
            cleaned_response = cleaned_response.strip()
            
            return {
                "response": cleaned_response, 
                "session_id": actual_session_id,
                "message": "Use this session_id in your next request to continue the conversation" if req.session_id is None else None
            }
        else:
            return {
                "response": "I received your query but couldn't generate a response.", 
                "session_id": actual_session_id
            }
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
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