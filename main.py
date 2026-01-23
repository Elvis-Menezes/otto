import http.client
import json

# Connect to LOCAL server, not the website!
conn = http.client.HTTPConnection("localhost", 8800)  # Changed from HTTPSConnection to HTTPConnection
payload = json.dumps({
  "composition_mode": "fluid",
  "description": "Technical Support Assistant",
  "max_engine_iterations": 3,
  "name": "Haxon",
  
})
headers = {
  'Content-Type': 'application/json',
  'Accept': 'application/json'
}
conn.request("POST", "/agents", payload, headers)
res = conn.getresponse()
data = res.read()
print(data.decode("utf-8"))