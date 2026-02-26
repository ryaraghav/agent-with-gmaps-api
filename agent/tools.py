import googlemaps 
import logging
from typing import Any, Dict, List, Optional
import os
from dotenv import load_dotenv

load_dotenv()

try:
    from .json_utils import print_json_table
except ImportError:
    from json_utils import print_json_table

# Set up logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# API Key
MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')

# Initialize Google Maps client
gmaps_client = googlemaps.Client(key=MAPS_API_KEY)



# Fields to request from Google Places API (confirmed valid field names)
DETAIL_FIELDS = [
    "name", "formatted_address", "website", "rating", "user_ratings_total",
    "editorial_summary", "price_level", "opening_hours", "place_id", "formatted_phone_number",
    "reservable", "serves_breakfast", "serves_dinner", "serves_lunch", "serves_vegetarian_food", 
    "serves_wine", "takeout", "serves_brunch", "serves_beer", "business_status",
    "curbside_pickup", "wheelchair_accessible_entrance", "current_opening_hours",
    "reviews"
]

def get_restaurants(
    *,
    place_id: Optional[str] = None,
    query: Optional[str] = None, #eg - hip bars
    location: Optional[str] = None, #eg - San Francisco, CA
    place_type: str = "restaurant", #eg - restaurant, bar, cafe, etc. 
    #TO DO: query and place type seem redundant, can we remove one?
    max_results: int = 10,
) -> Dict[str, Any]:
    """
    Simple restaurant search function.
    Returns: {"status": "OK", "results": List[Dict]}
    """
    try:
        # Direct place lookup by ID
        if place_id:
            resp = gmaps_client.place(place_id=place_id, fields=DETAIL_FIELDS)
            if resp.get("status") == "OK":
                return {"status": "OK", "results": [resp.get("result", {})]}
            return {"status": resp.get("status"), "results": [], "error_message": resp.get("error_message")}

        # Build search query
        search_parts = [query, place_type, location]
        search_query = " ".join(filter(None, search_parts))
        
        # Search for places
        places = gmaps_client.places(query=search_query)
        if places.get("status") != "OK":
            return {"status": places.get("status"), "results": [], "error_message": places.get("error_message")}
        
        results = places.get("results", [])[:max_results]
        
        # Get detailed info for each place
        detailed_results = []
        for place in results:
            place_id = place.get("place_id")
            if place_id:
                try:
                    detail = gmaps_client.place(place_id=place_id, fields=DETAIL_FIELDS)
                    if detail.get("status") == "OK":
                        detailed_results.append(detail.get("result", {}))
                    else:
                        detailed_results.append(place)  # fallback to basic info
                except:
                    detailed_results.append(place)  # fallback to basic info
            else:
                detailed_results.append(place)
        
        return {"status": "OK", "results": detailed_results}

    except Exception as e:
        return {"status": "ERROR", "results": [], "error_message": str(e)}


def print_restaurant_table(data: Dict[str, Any], title: str = "Restaurant Results") -> str:
    """
    Print restaurant data in a formatted table and return a summary string.
    This function is designed to be used as a tool by the agent.
    """
    try:
        print_json_table(data, title)
        
        # Return a summary for the agent to use
        if data.get("status") != "OK":
            return f"❌ Error: {data.get('error_message', 'Unknown error')}"
        
        results = data.get("result", data.get("results", []))
        if not results:
            return "📭 No restaurants found matching your criteria."
        
        summary_lines = [f"✅ Found {len(results)} restaurants:"]
        for i, restaurant in enumerate(results, 1):
            name = restaurant.get('name', 'N/A')
            rating = restaurant.get('rating', 'N/A')
            address = restaurant.get('formatted_address', 'N/A')
            summary_lines.append(f"{i}. {name} (Rating: {rating}/5) - {address}")
        
        return "\n".join(summary_lines)
        
    except Exception as e:
        return f"❌ Error displaying results: {str(e)}"


if __name__ == "__main__":
    # Simple test
    result = get_restaurants(query="cocktail bars", location="San Mateo, CA")
    print(result)
    #print_json_table(result, "Cocktail Bars")
    # 