import requests

url = "https://air-quality-api.open-meteo.com/v1/air-quality"
params = {
    "latitude": 52.52,
    "longitude": 13.41,
    "hourly": "pm10,pm2_5",
}
r = requests.get(url, params=params, timeout=10)
r.raise_for_status()
print(r.json()["hourly"]["pm2_5"][:5])