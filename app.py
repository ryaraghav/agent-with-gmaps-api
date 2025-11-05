from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

class Req(BaseModel):
    query: str
    from_: str | None = None

app = FastAPI()

@app.post("/run")
async def run(req: Req):
    """
    Get conversational restaurant recommendations.
    Returns natural language response with restaurant details.
    """
    try:
        from agent.tools import get_restaurants
        
        query = req.query.strip()
        location = req.from_ if req.from_ else None
        
        # Get restaurants using the agent's tool
        result = get_restaurants(query=query, location=location, max_results=5)
        
        # Check for errors
        if result.get("status") != "OK":
            error_msg = result.get("error_message", "Failed to fetch restaurants")
            return {"response": f"I apologize, but I encountered an issue while searching: {error_msg}"}
        
        restaurants = result.get("results", [])
        if not restaurants:
            return {"response": f"I couldn't find any restaurants matching '{query}'" + (f" in {location}" if location else "")}
        
        # Create a clean, conversational response
        response_parts = []
        if location:
            response_parts.append(f"I found {len(restaurants)} great options for {query} in {location}:")
        else:
            response_parts.append(f"I found {len(restaurants)} great options for {query}:")
        
        response_parts.append("")  # Blank line
        
        # Add restaurant details in clean format
        for i, restaurant in enumerate(restaurants, 1):
            name = restaurant.get("name", "Unknown")
            rating = restaurant.get("rating")
            address = restaurant.get("formatted_address", "Address not available")
            
            # Format price level
            price_level = restaurant.get("price_level")
            price_display = ""
            if price_level and price_level > 0:
                price_display = "$" * price_level
            
            # Get description/editorial summary
            description = ""
            if restaurant.get("editorial_summary"):
                if isinstance(restaurant["editorial_summary"], dict):
                    description = restaurant["editorial_summary"].get("overview", "").strip()
                else:
                    description = str(restaurant["editorial_summary"]).strip()
            
            # Build restaurant entry
            response_parts.append(f"{i}. {name}")
            
            # Rating and price on same line if both exist
            rating_price_line = []
            if rating:
                rating_price_line.append(f"⭐ {rating}/5")
            if price_display:
                rating_price_line.append(price_display)
            
            if rating_price_line:
                response_parts.append(f"   {' • '.join(rating_price_line)}")
            
            # Description if available
            if description:
                response_parts.append(f"   {description}")
            
            # Address
            response_parts.append(f"   📍 {address}")
            
            # Blank line between restaurants
            if i < len(restaurants):
                response_parts.append("")
        
        # Return conversational response
        return {"response": "\n".join(response_parts)}
        
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