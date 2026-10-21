import os, json, requests
from playwright.sync_api import sync_playwright

EVENT = "665480"
URL = f"https://www.ticket-onlineshop.com/ols/fcn/de/clubmaenner/channel/shop/areaplan/venue/event/{EVENT}"
BLOCKS = [7262186, 7262192, 7262198, 7262207, 7262213, 7262219]
TOPIC = os.environ["NTFY_TOPIC"]

data = {}
def on_response(r):
    if "/availability/" in r.url:
        try: data["a"] = r.json()
        except: pass

with sync_playwright() as p:
    b = p.chromium.launch()
    page = b.new_page(viewport={"width": 1400, "height": 900})
    page.on("response", on_response)
    page.goto(URL, timeout=120000)
    try: page.get_by_text("Jetzt Plätze auswählen").first.click(timeout=30000)
    except: print("Button nicht gefunden")
    page.wait_for_timeout(15000)
    b.close()

if "a" not in data:
    msg = "Test: keine Verfügbarkeitsdaten bekommen"
else:
    total, free = 0, {}
    for delta, n in data["a"]["generalAdmissions"]:
        total += delta
        free[total // 1000000] = n
    msg = "Test OK: " + ", ".join(f"{k}: {free.get(k,'?')}" for k in BLOCKS)

print(msg)
requests.post(f"https://ntfy.sh/{TOPIC}", data=msg.encode())
