"""
JSON visualization utilities for better output formatting
"""
import json
from typing import Dict, Any, List
import sys

def print_json_table(data: Dict[str, Any], title: str = "Results") -> None:
    """
    Print JSON data in a table-like format for better readability
    """
    print(f"\n{'='*80}")
    print(f"📊 {title}")
    print(f"{'='*80}")
    
    if data.get("status") != "OK":
        print(f"❌ Status: {data.get('status')}")
        print(f"💬 Message: {data.get('error_message', 'No error message')}")
        print(f"{'='*80}\n")
        return
    
    results = data.get("result", data.get("results", []))
    if not results:
        print("📭 No results found")
        print(f"{'='*80}\n")
        return
    
    print(f"✅ Found {len(results)} results\n")
    
    for i, restaurant in enumerate(results, 1):
        print(f"🍽️  Restaurant #{i}")
        print(f"   📛 Name: {restaurant.get('name', 'N/A')}")
        print(f"   📍 Address: {restaurant.get('formatted_address', 'N/A')}")
        print(f"   ⭐ Rating: {restaurant.get('rating', 'N/A')}/5 ({restaurant.get('user_ratings_total', 0)} reviews)")
        print(f"   💰 Price Level: {'$' * restaurant.get('price_level', 0) if restaurant.get('price_level') else 'N/A'}")
        print(f"   🌐 Website: {restaurant.get('website', 'N/A')}")
        print(f"   📞 Phone: {restaurant.get('formatted_phone_number', 'N/A')}")
        print(f"   🏷️  Types: {', '.join(restaurant.get('types', []))}")
        print(f"   🆔 Place ID: {restaurant.get('place_id', 'N/A')}")
        print(f"   🏢 Business Status: {restaurant.get('business_status', 'N/A')}")
        
        # Opening hours
        if restaurant.get('opening_hours'):
            hours = restaurant['opening_hours']
            print(f"   🕒 Open Now: {'Yes' if hours.get('open_now') else 'No'}")
            if hours.get('weekday_text'):
                print(f"   📅 Hours: {hours['weekday_text'][0] if hours['weekday_text'] else 'N/A'}")
        
        # Photos
        if restaurant.get('photos'):
            print(f"   📸 Photos: {len(restaurant['photos'])} available")
        
        # Geometry (location)
        if restaurant.get('geometry', {}).get('location'):
            loc = restaurant['geometry']['location']
            print(f"   📍 Coordinates: {loc.get('lat', 'N/A')}, {loc.get('lng', 'N/A')}")
        
        # Additional service and amenity fields (only valid ones)
        if restaurant.get('editorial_summary'):
            print(f"   📰 Editorial Summary: {restaurant.get('editorial_summary', 'N/A')}")
        
        # Dining options (only valid fields)
        dining_options = []
        if restaurant.get('serves_breakfast'): dining_options.append("Breakfast")
        if restaurant.get('serves_lunch'): dining_options.append("Lunch")
        if restaurant.get('serves_dinner'): dining_options.append("Dinner")
        if restaurant.get('serves_brunch'): dining_options.append("Brunch")
        if dining_options:
            print(f"   🍽️  Serves: {', '.join(dining_options)}")
        
        # Beverage options (only valid fields)
        beverage_options = []
        if restaurant.get('serves_beer'): beverage_options.append("Beer")
        if restaurant.get('serves_wine'): beverage_options.append("Wine")
        if beverage_options:
            print(f"   🍷 Beverages: {', '.join(beverage_options)}")
        
        # Food options (only valid fields)
        food_options = []
        if restaurant.get('serves_vegetarian_food'): food_options.append("Vegetarian")
        if food_options:
            print(f"   🥗 Food Options: {', '.join(food_options)}")
        
        # Service options (only valid fields)
        service_options = []
        if restaurant.get('takeout'): service_options.append("Takeout")
        if restaurant.get('reservable'): service_options.append("Reservations")
        if restaurant.get('delivery'): service_options.append("Delivery")
        if restaurant.get('dine_in'): service_options.append("Dine-in")
        if restaurant.get('curbside_pickup'): service_options.append("Curbside Pickup")
        if service_options:
            print(f"   🛎️  Services: {', '.join(service_options)}")
        
        # Accessibility
        if restaurant.get('wheelchair_accessible_entrance'):
            print(f"   ♿ Wheelchair Accessible: Yes")
        
        # Additional fields
        if restaurant.get('url'):
            print(f"   🔗 Google Maps URL: {restaurant.get('url', 'N/A')}")
        
        if restaurant.get('reviews'):
            print(f"   📝 Reviews: {len(restaurant['reviews'])} available")
        
        # Current opening hours (more detailed)
        if restaurant.get('current_opening_hours'):
            current_hours = restaurant['current_opening_hours']
            if current_hours.get('open_now') is not None:
                print(f"   🕒 Currently Open: {'Yes' if current_hours.get('open_now') else 'No'}")
            if current_hours.get('weekday_text'):
                print(f"   📅 Current Hours: {current_hours['weekday_text'][0] if current_hours['weekday_text'] else 'N/A'}")
        
        print("-" * 60)
    
    print(f"{'='*80}\n")


def print_json_summary(data: Dict[str, Any], title: str = "Summary") -> None:
    """
    Print a summary of the JSON data
    """
    print(f"\n{'='*60}")
    print(f"📋 {title}")
    print(f"{'='*60}")
    
    status = data.get("status", "UNKNOWN")
    results = data.get("result", data.get("results", []))
    
    print(f"Status: {status}")
    print(f"Number of results: {len(results) if isinstance(results, list) else 'N/A'}")
    
    if status == "OK" and results:
        # Calculate average rating
        ratings = [r.get('rating', 0) for r in results if r.get('rating')]
        avg_rating = sum(ratings) / len(ratings) if ratings else 0
        print(f"Average rating: {avg_rating:.1f}/5")
        
        # Count price levels
        price_levels = [r.get('price_level', 0) for r in results if r.get('price_level')]
        if price_levels:
            price_dist = {}
            for level in price_levels:
                price_dist[level] = price_dist.get(level, 0) + 1
            print(f"Price distribution: {price_dist}")
    
    print(f"{'='*60}\n")


def save_json_to_file(data: Dict[str, Any], filename: str = "restaurant_results.json") -> None:
    """
    Save JSON data to a file
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"💾 Results saved to: {filename}")
    except Exception as e:
        print(f"❌ Error saving to file: {e}")


def interactive_json_viewer(data: Dict[str, Any]) -> None:
    """
    Interactive JSON viewer with options
    """
    while True:
        print("\n" + "="*50)
        print("🔍 JSON Viewer Options:")
        print("1. Pretty print JSON")
        print("2. Table format")
        print("3. Summary")
        print("4. Save to file")
        print("5. Exit")
        print("="*50)
        
        choice = input("Choose an option (1-5): ").strip()
        
        if choice == "1":
            print(json.dumps(data, indent=2, ensure_ascii=False))
        elif choice == "2":
            print_json_table(data, "Table View")
        elif choice == "3":
            print_json_summary(data, "Data Summary")
        elif choice == "4":
            filename = input("Enter filename (default: restaurant_results.json): ").strip()
            if not filename:
                filename = "restaurant_results.json"
            save_json_to_file(data, filename)
        elif choice == "5":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please try again.")


if __name__ == "__main__":
    # Example usage
    sample_data = {
        "status": "OK",
        "result": [
            {
                "name": "Sample Restaurant",
                "formatted_address": "123 Main St, City, State",
                "rating": 4.5,
                "user_ratings_total": 150,
                "price_level": 2,
                "website": "https://example.com",
                "types": ["restaurant", "food", "establishment"]
            }
        ]
    }
    
    print("🧪 Testing JSON utilities...")
    print_json_table(sample_data, "Sample Data")
    print_json_summary(sample_data, "Sample Summary")
