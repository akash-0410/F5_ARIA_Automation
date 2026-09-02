"""
Shared auth helper for the bootstrap scripts. UNVERIFIED — mirrors the
refresh-token -> Bearer exchange proven live in wrapper_scripts_raw/f5_vra_run_action.js,
but has not itself been executed against a real tenant.

Flow (VMware-documented for Aria Automation 8.x on-prem):
  1. POST /csp/gateway/am/api/login with username/password/domain -> refresh_token
  2. POST /iaas/api/login with the refresh_token -> short-lived Bearer access token
Both vRA (Assembler/ABX) and the embedded vRO share this same identity broker,
so one token pair is reused for both bootstrap scripts.
"""
import sys
import requests


def get_bearer_token(host, username, password, domain, verify_tls=True):
    session = requests.Session()
    session.verify = verify_tls

    login_resp = session.post(
        f"https://{host}/csp/gateway/am/api/login",
        json={"username": username, "password": password, "domain": domain},
        timeout=30,
    )
    if login_resp.status_code != 200:
        print(f"[FATAL] /csp/gateway/am/api/login failed: {login_resp.status_code} {login_resp.text}", file=sys.stderr)
        sys.exit(1)
    refresh_token = login_resp.json().get("refresh_token")
    if not refresh_token:
        print("[FATAL] Login succeeded but no refresh_token in response body.", file=sys.stderr)
        sys.exit(1)

    exchange_resp = session.post(
        f"https://{host}/iaas/api/login",
        json={"refreshToken": refresh_token},
        timeout=30,
    )
    if exchange_resp.status_code != 200:
        print(f"[FATAL] /iaas/api/login exchange failed: {exchange_resp.status_code} {exchange_resp.text}", file=sys.stderr)
        sys.exit(1)
    token = exchange_resp.json().get("token")
    if not token:
        print("[FATAL] Token exchange succeeded but no token in response body.", file=sys.stderr)
        sys.exit(1)
    return token


def bearer_session(host, username, password, domain, verify_tls=True):
    token = get_bearer_token(host, username, password, domain, verify_tls=verify_tls)
    session = requests.Session()
    session.verify = verify_tls
    session.headers.update({
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    })
    return session
