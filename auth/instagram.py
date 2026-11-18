#!/usr/bin/env python3
"""Check the Instagram token in .env and fill INSTAGRAM_USER_ID.

  auth/instagram.py      # run once after pasting a token into .env

Supports both token kinds, chosen by config.json instagram.host:
  graph.facebook.com   - system user token from Business settings (EAA...); never expires
  graph.instagram.com  - token from the app dashboard (IGAA...); 60 days, refresh() extends it
Tokens are never printed.
"""
import json, re, sys, urllib.parse, urllib.request, urllib.error
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from core.common import ROOT, CFG, need

HOST = CFG["instagram"]["host"]
G = f"https://{HOST}/{CFG['instagram']['graph_version']}"
ENV = ROOT / ".env"
NEEDED = {"instagram_basic", "instagram_content_publish"}


def get(url, **q):
    try:
        with urllib.request.urlopen(f"{url}?" + urllib.parse.urlencode(q), timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read() or b"{}"
        try:
            msg = json.loads(body).get("error", {}).get("message", "")
        except ValueError:
            msg = body.decode()[:300]
        raise RuntimeError(f"error {e.code}: {msg}")


def set_env(key, val):
    import os
    s = ENV.read_text()
    line = f"{key}={val}"
    s = re.sub(rf"^{key}=.*$", lambda _: line, s, flags=re.M) if re.search(rf"^{key}=", s, re.M) \
        else s.rstrip("\n") + "\n" + line + "\n"
    ENV.write_text(s)
    os.environ[key] = val


def refresh():
    """Return a valid token; Instagram-login tokens are extended by 60 days when allowed."""
    tok = need("INSTAGRAM_ACCESS_TOKEN")
    if HOST != "graph.instagram.com":
        return tok                                   # system user tokens do not expire
    try:
        new = get(f"https://{HOST}/refresh_access_token", grant_type="ig_refresh_token", access_token=tok)["access_token"]
        if new != tok:
            set_env("INSTAGRAM_ACCESS_TOKEN", new)
        return new
    except RuntimeError:
        return tok                                   # too new to refresh (<24h) - still valid


def facebook(tok):
    import os
    known = (os.environ.get("INSTAGRAM_USER_ID") or "").split("#")[0].strip()
    if known:                                    # id pasted from Business settings: just confirm access
        ig = get(f"{G}/{known}", fields="id,username", access_token=tok)
        return ig["id"], ig["username"], "id from .env"
    perms = {p["permission"] for p in get(f"{G}/me/permissions", access_token=tok)["data"] if p["status"] == "granted"}
    if NEEDED - perms:
        raise SystemExit(f"Token is missing: {', '.join(sorted(NEEDED - perms))} (has: {', '.join(sorted(perms)) or 'none'}).\n"
                         "Generate a new system user token with those permissions ticked.")
    pages = get(f"{G}/me/accounts", fields="name,instagram_business_account{id,username}", access_token=tok)["data"]
    linked = [p for p in pages if p.get("instagram_business_account")]
    if not linked:
        raise SystemExit(f"No Page with a linked Instagram account is visible to this token (Pages: "
                         f"{', '.join(p['name'] for p in pages) or 'none'}).\nIn Business settings > System users, "
                         "assign the Facebook Page (and the Instagram account) to the system user, then rerun.")
    if len(linked) > 1:
        print("Several linked accounts; using the first:", ", ".join(p["instagram_business_account"]["username"] for p in linked))
    ig = linked[0]["instagram_business_account"]
    return ig["id"], ig["username"], f"via Page '{linked[0]['name']}'"


def instagram(tok):
    me = get(f"{G}/me", fields="user_id,username,account_type", access_token=tok)
    refresh()
    return str(me["user_id"]), me["username"], me.get("account_type", "")


def main():
    tok = need("INSTAGRAM_ACCESS_TOKEN")
    try:
        uid, name, note = (instagram if HOST == "graph.instagram.com" else facebook)(tok)
    except RuntimeError as e:
        raise SystemExit(f"Token check failed - {e}")
    set_env("INSTAGRAM_USER_ID", uid)
    print(f"Token works for @{name} ({note}); saved INSTAGRAM_USER_ID {uid} to .env")


if __name__ == "__main__":
    main()
