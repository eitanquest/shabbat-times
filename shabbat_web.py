"""
Shabbat Times Web App
=====================
Run with: python3 shabbat_web.py
Then open: http://localhost:5001
"""

import json
import urllib.request
from http.server import HTTPServer, BaseHTTPRequestHandler

# ---------------------------------------------------------------------------
# City configuration (Eitan's verified weekly list)
# ---------------------------------------------------------------------------
DEFAULT_CITIES = [
    {"name": "Jerusalem, Israel",    "geonameid": 281184,  "b": 40},
    {"name": "Tel Aviv, Israel",     "geonameid": 293397,  "b": 22},
    {"name": "Pardes Hanna, Israel", "lat": 32.4706, "lon": 34.9692, "tzid": "Asia/Jerusalem", "b": 30},
    {"name": "Safed, Israel",        "lat": 32.9646, "lon": 35.4956, "tzid": "Asia/Jerusalem", "b": 30},
    {"name": "Katzrin, Israel",      "lat": 32.9946, "lon": 35.6925, "tzid": "Asia/Jerusalem", "b": 30},
    {"name": "New York City, USA",   "geonameid": 5128581, "b": 18},
    {"name": "New Paltz, NY, USA",   "zip": "12561",       "b": 18},
    {"name": "Baltimore, MD, USA",   "geonameid": 4347778, "b": 18},
    {"name": "Boulder, CO, USA",     "geonameid": 5574991, "b": 18},
    {"name": "Austin, TX, USA",      "geonameid": 4671654, "b": 18},
    {"name": "Berkeley, CA, USA",    "geonameid": 5327684, "b": 18},
    {"name": "Los Angeles, CA, USA", "geonameid": 5368361, "b": 18},
    {"name": "Uman, Ukraine",        "lat": 48.7451, "lon": 30.2218, "tzid": "Europe/Kiev",    "b": 18},
    {"name": "Vienna, Austria",      "geonameid": 2761369, "b": 18},
    {"name": "London, England",      "geonameid": 2643743, "b": 18},
    {"name": "Prague, Czech Rep",    "geonameid": 3067696, "b": 18},
    {"name": "Cape Town, SA",        "geonameid": 3369157, "b": 18},
    {"name": "Panama City, Panama",  "geonameid": 3703443, "b": 18},
    {"name": "Tehran, Iran",         "geonameid": 112931,  "b": 18},
    {"name": "Paris, France",        "geonameid": 2988507, "b": 18},
]

def _build_url(city):
    b = city["b"]
    if "geonameid" in city:
        return f"https://www.hebcal.com/shabbat?cfg=json&geonameid={city['geonameid']}&M=on&b={b}&leyning=off"
    elif "zip" in city:
        return f"https://www.hebcal.com/shabbat?cfg=json&zip={city['zip']}&M=on&b={b}&leyning=off"
    else:
        return f"https://www.hebcal.com/shabbat?cfg=json&latitude={city['lat']}&longitude={city['lon']}&tzid={city['tzid']}&M=on&b={b}&leyning=off"

def _fmt_time(t):
    if ":" in t and len(t) == 5:
        h, m = int(t[:2]), t[3:]
        suffix = "AM" if h < 12 else "PM"
        h12 = h % 12 or 12
        return f"{h12}:{m} {suffix}"
    return t

def fetch_shabbat_times():
    parasha = ""
    results = []
    for city in DEFAULT_CITIES:
        req = urllib.request.Request(_build_url(city), headers={"User-Agent": "ShabbatTimesWeb/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                data = json.loads(r.read())
        except Exception as e:
            results.append({"name": city["name"], "b": city["b"], "candle": "ERROR"})
            continue
        items = data.get("items", [])
        candle = next((i for i in items if i["category"] == "candles"), None)
        par    = next((i for i in items if i["category"] == "parashat"), None)
        if par and not parasha:
            parasha = par["title"]
        raw = candle["title"].split(": ", 1)[1] if candle else "N/A"
        results.append({"name": city["name"], "b": city["b"], "candle": _fmt_time(raw)})
    return parasha, results

HOME_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Shabbat Times</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
         background: #f5f0e8; min-height: 100vh;
         display: flex; align-items: center; justify-content: center; padding: 20px; }
  .container { max-width: 480px; width: 100%; text-align: center; }
  h1 { font-size: 2rem; color: #2c1810; margin-bottom: 8px; }
  .subtitle { color: #7a5c3a; margin-bottom: 40px; font-size: 1rem; }
  .fetch-btn { width: 100%; padding: 18px; background: #2c1810; color: white;
               border: none; border-radius: 12px; font-size: 1.1rem;
               cursor: pointer; transition: background 0.2s; }
  .fetch-btn:hover { background: #4a2e1a; }
  .fetch-btn:disabled { background: #a08060; cursor: not-allowed; }
  #status { margin-top: 20px; color: #7a5c3a; font-size: 0.9rem; min-height: 24px; }
  .card { background: white; border-radius: 12px; box-shadow: 0 2px 12px rgba(0,0,0,0.08);
          overflow: hidden; margin-top: 28px; display: none; text-align: left; }
  .parasha-header { padding: 14px 20px; background: #2c1810; color: #f5f0e8;
                    font-size: 1rem; font-weight: 600; }
  .city-row { display: flex; justify-content: space-between; align-items: center;
              padding: 11px 20px; border-bottom: 1px solid #f0ebe3; }
  .city-row:last-child { border-bottom: none; }
  .city-name { color: #2c1810; font-size: 0.9rem; }
  .right { display: flex; align-items: center; gap: 8px; }
  .time { font-weight: 600; color: #2c1810; font-size: 0.9rem; }
  .offset { font-size: 0.72rem; color: #a08060; }
  .copy-btn { margin-top: 16px; width: 100%; padding: 14px;
              background: #5a8a5a; color: white; border: none; border-radius: 8px;
              font-size: 0.95rem; cursor: pointer; transition: background 0.2s; display: none; }
  .copy-btn:hover { background: #3d6b3d; }
  .copy-btn.copied { background: #3d6b3d; }
  .source { margin-top: 10px; text-align: center; font-size: 0.72rem; color: #a08060; }
</style>
</head>
<body>
<div class="container">
  <h1>🕯️ Shabbat Times</h1>
  <p class="subtitle">Live candle lighting times for 20 cities worldwide</p>
  <button class="fetch-btn" onclick="fetchTimes()">Get This Week's Times</button>
  <div id="status"></div>
  <div class="card" id="card"></div>
  <button class="copy-btn" id="copyBtn" onclick="copyList()">Copy as Text List</button>
  <div class="source" id="source"></div>
</div>
<script>
  let plainText = '';

  async function fetchTimes() {
    const btn = document.querySelector('.fetch-btn');
    const status = document.getElementById('status');
    btn.disabled = true;
    btn.textContent = 'Fetching times…';
    status.textContent = 'Contacting HebCal for all 20 cities…';

    try {
      const res = await fetch('/api/times');
      const data = await res.json();

      const card = document.getElementById('card');
      card.innerHTML = `<div class="parasha-header">${data.parasha}</div>` +
        data.results.map(r =>
          `<div class="city-row">
            <span class="city-name">${r.name}</span>
            <span class="right">
              <span class="time">${r.candle}</span>
              <span class="offset">(+${r.b})</span>
            </span>
          </div>`
        ).join('');
      card.style.display = 'block';

      plainText = data.parasha + '\\n\\n' +
        data.results.map(r => `${r.name} ${r.candle} (+${r.b})`).join('\\n') +
        '\\n\\nSource: HebCal — confirm times before Shabbat.';

      document.getElementById('copyBtn').style.display = 'block';
      document.getElementById('source').textContent = 'Source: HebCal — confirm times before Shabbat.';
      status.textContent = '';
      btn.textContent = 'Refresh Times';
      btn.disabled = false;
    } catch(e) {
      status.textContent = 'Error fetching times. Is the server running?';
      btn.textContent = 'Get This Week\\'s Times';
      btn.disabled = false;
    }
  }

  function copyList() {
    navigator.clipboard.writeText(plainText).then(() => {
      const btn = document.getElementById('copyBtn');
      btn.textContent = '✓ Copied!';
      btn.classList.add('copied');
      setTimeout(() => { btn.textContent = 'Copy as Text List'; btn.classList.remove('copied'); }, 2000);
    });
  }
</script>
</body>
</html>"""

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/api/times':
            parasha, results = fetch_shabbat_times()
            payload = json.dumps({"parasha": parasha, "results": results})
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(payload.encode())
        else:
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(HOME_PAGE.encode())

    def log_message(self, format, *args):
        pass

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5001))
    print(f"Shabbat Times running at http://localhost:{port}")
    HTTPServer(("", port), Handler).serve_forever()
