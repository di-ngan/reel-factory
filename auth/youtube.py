#!/usr/bin/env python3
"""YouTube sign-in (OAuth for the YouTube Data API v3, no extra packages). publish/youtube.py uses it.

  auth/youtube.py          # sign in once in the browser and save the token to secrets/youtube_token.json

One-time setup: Google Cloud console -> new project -> enable "YouTube Data API v3" ->
OAuth consent screen (External, add yourself as a test user) -> Credentials -> OAuth client ID ->
"Desktop app" -> download JSON to secrets/youtube_client.json.
Note: until Google audits the project, uploads through the API are locked to private.
"""
import http.server, json, secrets, sys, urllib.parse, urllib.request, webbrowser
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.common import ROOT

CLIENT = ROOT / "secrets" / "youtube_client.json"
TOKEN = ROOT / "secrets" / "youtube_token.json"
SCOPE = "https://www.googleapis.com/auth/youtube.upload"


def post_form(url, data):
    req = urllib.request.Request(url, data=urllib.parse.urlencode(data).encode(), method="POST")
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


def client():
    if not CLIENT.exists():
        raise SystemExit(f"Missing {CLIENT} - see the setup notes at the top of this script.")
    c = json.loads(CLIENT.read_text())
    return c.get("installed") or c.get("web")


def sign_in():
    c = client()
    state, code = secrets.token_urlsafe(16), {}

    class H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            if q.get("state", [""])[0] == state:
                code["v"] = q.get("code", [""])[0]
            self.send_response(200); self.end_headers()
            self.wfile.write(b"Signed in. You can close this tab.")
        def log_message(self, *a):
            pass

    srv = http.server.HTTPServer(("127.0.0.1", 0), H)
    redirect = f"http://127.0.0.1:{srv.server_port}"
    url = "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode({
        "client_id": c["client_id"], "redirect_uri": redirect, "response_type": "code", "scope": SCOPE,
        "access_type": "offline", "prompt": "consent", "state": state})
    print("Opening the Google sign-in page. If it does not open, visit:\n" + url)
    webbrowser.open(url)
    while "v" not in code:
        srv.handle_request()
    tok = post_form(c["token_uri"], {"code": code["v"], "client_id": c["client_id"], "client_secret": c["client_secret"],
                                     "redirect_uri": redirect, "grant_type": "authorization_code"})
    TOKEN.parent.mkdir(exist_ok=True)
    TOKEN.write_text(json.dumps(tok))
    TOKEN.chmod(0o600)
    print("Saved", TOKEN)


def access_token():
    if not TOKEN.exists():
        sign_in()
    tok = json.loads(TOKEN.read_text())
    c = client()
    new = post_form(c["token_uri"], {"refresh_token": tok["refresh_token"], "client_id": c["client_id"],
                                     "client_secret": c["client_secret"], "grant_type": "refresh_token"})
    return new["access_token"]


if __name__ == "__main__":
    sign_in()
