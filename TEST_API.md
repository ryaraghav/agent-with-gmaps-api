# 🧪 Testing the FastAPI Endpoint

## 🚀 Step 1: Start the Server

```bash
cd /Users/Aishwaryara/Projects/GitHub/agent-with-gmaps-api
source myvenv/bin/activate
python start_server.py
```

Or directly:
```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

## 📍 Endpoints Available

### 1. `/run` - Get structured restaurant data
- **Method**: POST
- **Returns**: JSON array of restaurants with details

### 2. `/agent-response` - Get formatted agent response
- **Method**: POST
- **Returns**: Formatted text response

### 3. `/docs` - Interactive API documentation
- **Method**: GET
- **Browser**: Open http://localhost:8000/docs

## 🔑 Authentication

All endpoints require this header:
```
Authorization: Bearer SHARED_SECRET_123
```

## 🧪 Test Methods

### Method 1: Using FastAPI Interactive Docs (Easiest)

1. Start the server
2. Open browser: http://localhost:8000/docs
3. Click on `/run` endpoint
4. Click "Try it out"
5. Enter:
   ```json
   {
     "query": "Italian restaurants",
     "from_": "San Francisco"
   }
   ```
6. Click "Execute"
7. See the response!

### Method 2: Using curl

```bash
# Test /run endpoint
curl -X POST "http://localhost:8000/run" \
  -H "Authorization: Bearer SHARED_SECRET_123" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Italian restaurants",
    "from_": "San Francisco"
  }'

# Test /agent-response endpoint
curl -X POST "http://localhost:8000/agent-response" \
  -H "Authorization: Bearer SHARED_SECRET_123" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "coffee shops",
    "from_": "San Bruno"
  }'
```

### Method 3: Using Python requests

```python
import requests

url = "http://localhost:8000/run"
headers = {
    "Authorization": "Bearer SHARED_SECRET_123",
    "Content-Type": "application/json"
}
data = {
    "query": "Italian restaurants",
    "from_": "San Francisco"
}

response = requests.post(url, json=data, headers=headers)
print(response.json())
```

### Method 4: Using httpie (if installed)

```bash
pip install httpie

http POST localhost:8000/run \
  Authorization:"Bearer SHARED_SECRET_123" \
  query="coffee shops" \
  from_="San Bruno"
```

## 📋 Example Requests

### Example 1: Find restaurants by cuisine
```json
{
  "query": "sushi restaurants",
  "from_": "New York"
}
```

### Example 2: Find coffee shops
```json
{
  "query": "coffee shops",
  "from_": "San Francisco"
}
```

### Example 3: Find bars
```json
{
  "query": "bars",
  "from_": "Seattle"
}
```

### Example 4: Query only (location in query)
```json
{
  "query": "Italian restaurants in Boston",
  "from_": null
}
```

## ✅ Expected Response Format

### `/run` endpoint response:
```json
[
  {
    "name": "Restaurant Name",
    "address": "123 Main St, City, State",
    "url": "https://restaurant.com",
    "price": "$$",
    "rating": 4.5,
    "phone": "+1 (555) 123-4567",
    "description": "Restaurant description...",
    "reservable": true,
    "serves_breakfast": false,
    "serves_lunch": true,
    "serves_dinner": true,
    "serves_brunch": false,
    "takeout": true,
    "wheelchair_accessible": true
  }
]
```

### `/agent-response` endpoint response:
```json
{
  "response": "✅ Found 5 restaurants:\n1. Restaurant Name (Rating: 4.5/5) - Address..."
}
```

## 🔍 Troubleshooting

### Error: "ModuleNotFoundError: No module named 'agent_integration'"
- Make sure you're running from the project root directory
- Check that `agent_integration.py` exists

### Error: "Unauthorized"
- Make sure you're including the Authorization header
- Check that it's exactly: `Bearer SHARED_SECRET_123`

### Error: "Internal server error"
- Check your `.env` file has `GOOGLE_MAPS_API_KEY`
- Check server logs for detailed error messages
- Verify Google Maps API is enabled in Google Cloud Console

### Server won't start
- Make sure virtual environment is activated
- Check port 8000 is not already in use: `lsof -i :8000`
- Install dependencies: `pip install -r requirements.txt`

## 🌐 Exposing to Internet (ngrok)

Once local testing works:

```bash
# In a new terminal
ngrok http 8000
```

Use the ngrok URL (e.g., `https://abc123.ngrok.io`) as your `AGENT_ENDPOINT`

