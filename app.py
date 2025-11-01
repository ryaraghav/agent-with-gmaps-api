from fastapi import FastAPI
from pydantic import BaseModel
from agent_integration import process_restaurant_query, get_agent_response
import os
from dotenv import load_dotenv

load_dotenv()

class Req(BaseModel):
    query: str
    from_: str | None = None

app = FastAPI()

@app.post("/run")
def run(req: Req):
    # Authentication removed for testing
    try:
        # Use the agent integration to process the request
        restaurants = process_restaurant_query(req.query, req.from_)
        
        # Check if there's an error in the first item
        if restaurants and "error" in restaurants[0]:
            return {"error": restaurants[0]["error"]}
        
        return restaurants
        
    except Exception as e:
        return {"error": f"Internal server error: {str(e)}"}

@app.post("/agent-response")
def agent_response(req: Req):
    # Authentication removed for testing
    try:
        # Get formatted agent response
        response = get_agent_response(req.query, req.from_)
        return {"response": response}
        
    except Exception as e:
        return {"error": f"Internal server error: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)