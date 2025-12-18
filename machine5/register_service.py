import json, requests

with open('service_metier.json') as f:
    service = json.load(f)

requests.put('http://localhost:8500/v1/agent/service/register', json=service)
print("Service enregistré dans Consul")