import httpx

def lookup_ip(ip: str) -> dict:
    try:
        r = httpx.get(
            f"http://ip-api.com/json/{ip}",
            params={"fields": "status,country,city"},
            timeout=2,
        )
        data = r.json()
        if data.get("status") == "success":
            return {"country": data["country"], "city": data["city"]}
    except (httpx.HTTPError, ValueError):
        pass
    return {"country": None, "city": None}