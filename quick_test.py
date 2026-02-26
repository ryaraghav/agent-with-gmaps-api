import requests
import json

response = requests.post(
    "http://localhost:8000/agent-response",
    json={"query": "Italian restaurants in San Francisco"}
)

data = response.json()
print("=" * 60)
print("FULL RESPONSE:")
print("=" * 60)
print(data.get('response', ''))
print("=" * 60)