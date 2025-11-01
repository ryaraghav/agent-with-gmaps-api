"""
Agent integration for FastAPI
This module provides a way to use the agent programmatically
"""
from agent.tools import get_restaurants, print_restaurant_table
from agent.prompts import system_instruction_v4
import json
import re
from typing import Dict, List, Any

def process_restaurant_query(query: str, location: str = None) -> List[Dict[str, Any]]:
    """
    Process a restaurant query using the agent's logic
    """
    try:
        # Use the agent's restaurant search functionality
        result = get_restaurants(
            query=query,
            location=location,
            max_results=5
        )
        
        if result.get("status") != "OK":
            return [{"error": result.get("error_message", "Failed to fetch restaurants")}]
        
        # Format the response for the client
        restaurants = []
        for restaurant in result.get("results", []):
            restaurants.append({
                "name": restaurant.get("name", "N/A"),
                "address": restaurant.get("formatted_address", "N/A"),
                "url": restaurant.get("website", ""),
                "price": "$" * restaurant.get("price_level", 0) if restaurant.get("price_level") else "N/A",
                "rating": restaurant.get("rating", 0),
                "phone": restaurant.get("formatted_phone_number", ""),
                "description": restaurant.get("editorial_summary", ""),
                "reservable": restaurant.get("reservable", False),
                "serves_breakfast": restaurant.get("serves_breakfast", False),
                "serves_lunch": restaurant.get("serves_lunch", False),
                "serves_dinner": restaurant.get("serves_dinner", False),
                "serves_brunch": restaurant.get("serves_brunch", False),
                "takeout": restaurant.get("takeout", False),
                "wheelchair_accessible": restaurant.get("wheelchair_accessible_entrance", False)
            })
        
        return restaurants
        
    except Exception as e:
        return [{"error": f"Internal server error: {str(e)}"}]

def get_agent_response(query: str, location: str = None) -> str:
    """
    Get a formatted response from the agent
    """
    try:
        # Use the agent's tools to get data
        result = get_restaurants(
            query=query,
            location=location,
            max_results=5
        )
        
        # Use the print function to get formatted output
        formatted_output = print_restaurant_table(result, "Restaurant Search Results")
        
        return formatted_output
        
    except Exception as e:
        return f"Error: {str(e)}"
