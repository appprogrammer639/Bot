import os, re, json, datetime as dt, requests
from zoneinfo import ZoneInfo

URL = "https://www.fcn.de/news/artikel/tickets-fuer-heimspiele-des-1-fcn-hier-laeuft-der-vorverkauf/"
TOPIC = os.environ["NTFY_TOPIC"]
TZ = ZoneInfo("Europe/Berlin")
MONATE = ["Januar","Februar","März","April","Mai","Juni","Juli",
          "August","September","Oktober","November","Dezember"]

def senden(titel, text):
    requests.post(f"https://ntfy.sh/{TOPIC}", data=text.encode(),
                  headers={"Title": titel.encode("utf-8")})

try:
    state = json.load(open("state.json"))
except Exception:
    state = {"gesehen": [], "erinnert": []}

html = requests.get(URL, timeout=30, headers={"User-Agent": "Mozilla/5.0"}).text
text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html))

muster = (r"(\d{1,2})\.\s*(" + "|".join(MONATE) + r")[^.]{0,60}?"
          r"(\d{1,2})(?::(\d{2}))?\s*Uhr[^.]{0,80}?freie\w* Verkauf")
jetzt = dt.datetime.now(TZ)
geaendert = False

for tag, monat, std, minute in re.findall(muster, text):
    start = dt.datetime(jetzt.year, MONATE.index(monat) + 1, int(tag),
                        int(std), int(minute or 0), tzinfo=TZ)
    if start < jetzt - dt.timedelta(days=60):
        start = start.replace(year=jetzt.year + 1)
    key = start.isoformat()
    zeit = start.strftime("%d.%m. um %H:%M Uhr")

    if key not in state["gesehen"] and start > jetzt:
        senden("FCN: Neuer Vorverkauf!", f"Freier Verkauf startet am {zeit}.")
        state["gesehen"].append(key); geaendert = True

    if key not in state["erinnert"] and dt.timedelta(0) < start - jetzt <= dt.timedelta(minutes=35):
        senden("FCN: Gleich geht's los!", f"Freier Verkauf startet {zeit}. Ab in den Shop!")
        state["erinnert"].append(key); geaendert = True

if geaendert:
    json.dump(state, open("state.json", "w"))
print("Fertig, gefunden:", len(re.findall(muster, text)))
