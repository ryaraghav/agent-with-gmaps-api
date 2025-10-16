# 🍽️ Restaurant Finder Agent with Google Maps API

An intelligent AI agent that helps users find the best restaurants in any location using Google Maps API and Google's Agent Development Kit (ADK).

## 🌟 Features

- **Smart Location Detection**: Automatically extracts location information from user queries
- **Comprehensive Restaurant Search**: Finds restaurants with detailed information including ratings, hours, amenities, and more
- **Rich Data Display**: Beautiful table-formatted results with emojis and organized information
- **Flexible Search**: Support for various search types (restaurants, bars, cafes, etc.)
- **Real-time Information**: Current opening hours, business status, and availability
- **Detailed Restaurant Info**: Ratings, reviews, price levels, dining options, and accessibility features

## 🏗️ Project Structure

```
agent-with-gmaps-api/
├── agent/
│   ├── agent.py          # Main agent configuration
│   ├── tools.py          # Google Maps API integration
│   ├── prompts.py        # Agent instructions and prompts
│   └── json_utils.py     # JSON formatting and display utilities
├── myvenv/               # Python virtual environment
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Google Maps API key
- Google Cloud account (for ADK)

### Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd agent-with-gmaps-api
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv myvenv
   source myvenv/bin/activate  # On Windows: myvenv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the project root:
   ```bash
   GOOGLE_MAPS_API_KEY=your_google_maps_api_key_here
   ```

5. **Run the agent**
   ```bash
   adk run agent
   ```

## 🔧 Configuration

### Google Maps API Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the following APIs:
   - Places API
   - Maps JavaScript API
   - Geocoding API
4. Create credentials (API Key)
5. Add the API key to your `.env` file

### Agent Configuration

The agent is configured in `agent/agent.py`:

```python
root_agent = Agent(
    name="curator_agent",
    model="gemini-2.0-flash",
    description="Help user find the best restaurants in a city",
    instruction=prompts.system_instruction_v3,
    tools=[tools.get_restaurants]
)
```

## 📖 Usage Examples

### Basic Restaurant Search
```
User: "Find me some good restaurants in San Francisco"
Agent: I'll search for restaurants in San Francisco
```

### Specific Cuisine Search
```
User: "I want Italian restaurants near Central Park in New York"
Agent: I'll search for Italian restaurants near Central Park in New York
```

### Time-Specific Search
```
User: "Find restaurants open for dinner in downtown Seattle"
Agent: I'll search for restaurants open for dinner in downtown Seattle
```

## 🛠️ API Reference

### `get_restaurants()` Function

The main search function with the following parameters:

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `place_id` | str (optional) | Direct lookup by Google Place ID | "ChIJN1t_tDeuEmsRUsoyG83frY4" |
| `query` | str (optional) | Search query (cuisine, type, etc.) | "Italian restaurants", "cocktail bars" |
| `location` | str (optional) | Location to search in | "San Francisco, CA", "New York" |
| `place_type` | str | Type of place (default: "restaurant") | "restaurant", "bar", "cafe" |
| `max_results` | int | Maximum number of results (default: 5) | 5, 10, 20 |

### Response Format

```json
{
  "status": "OK",
  "results": [
    {
      "name": "Restaurant Name",
      "formatted_address": "123 Main St, City, State",
      "rating": 4.5,
      "user_ratings_total": 150,
      "price_level": 2,
      "website": "https://restaurant.com",
      "formatted_phone_number": "+1 (555) 123-4567",
      "opening_hours": {
        "open_now": true,
        "weekday_text": ["Monday: 11:00 AM – 10:00 PM", ...]
      },
      "editorial_summary": "Popular restaurant description...",
      "place_id": "ChIJN1t_tDeuEmsRUsoyG83frY4",
      "business_status": "OPERATIONAL"
    }
  ]
}
```

## 🎯 Key Features Explained

### Smart Location Detection

The agent uses advanced prompt engineering to detect locations in various formats:
- City names: "San Francisco", "New York"
- State combinations: "Austin, TX", "Seattle, WA"
- Neighborhoods: "downtown Seattle", "near Central Park"
- Relative locations: "around Times Square", "in the Mission District"

### Comprehensive Restaurant Data

Each restaurant result includes:
- **Basic Info**: Name, address, phone, website
- **Ratings**: Star rating and review count
- **Pricing**: Price level indicators ($, $$, $$$, $$$$)
- **Hours**: Current status and weekly schedule
- **Services**: Takeout, delivery, reservations, curbside pickup
- **Dining Options**: Breakfast, lunch, dinner, brunch availability
- **Beverages**: Beer, wine availability
- **Accessibility**: Wheelchair accessible entrance
- **Business Status**: Currently operational, temporarily closed, etc.

### Rich Display Format

The `json_utils.py` module provides beautiful formatting:
- 📊 Table-style display with emojis
- 📋 Summary statistics
- 💾 Save results to JSON file
- 🔍 Interactive viewer options

## 🧪 Testing

### Test the Tools Module
```bash
cd agent
python tools.py
```

### Test JSON Utilities
```bash
cd agent
python json_utils.py
```

## 🔍 Troubleshooting

### Common Issues

1. **API Key Not Working**
   - Verify the API key is correct in `.env`
   - Check that required APIs are enabled in Google Cloud Console
   - Ensure billing is set up for your Google Cloud project

2. **No Results Found**
   - Try broader location terms
   - Check if the location exists in Google Maps
   - Verify the search query is clear

3. **Agent Not Responding**
   - Check that ADK is properly installed
   - Verify the virtual environment is activated
   - Check the agent configuration in `agent.py`

### Debug Mode

Enable debug logging by modifying `tools.py`:
```python
logging.basicConfig(level=logging.DEBUG)
```

## 📝 Dependencies

- `google-genai`: Google's Generative AI SDK
- `google-adk`: Google's Agent Development Kit
- `googlemaps`: Google Maps API client
- `python-dotenv`: Environment variable management

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Google Maps API for comprehensive location data
- Google's Agent Development Kit for AI agent framework
- The open-source community for inspiration and tools

## 📞 Support

If you encounter any issues or have questions:
1. Check the troubleshooting section above
2. Review the Google Maps API documentation
3. Open an issue in this repository

---

**Happy restaurant hunting! 🍽️✨**
