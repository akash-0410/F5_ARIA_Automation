"""
ABX Action: f5_read_virtual_server
-------------------------------------
Custom Resource "Read" lifecycle action for F5.VirtualServer. vRA calls this
to refresh/resync the resource's properties (day-2 "Sync"/periodic refresh)
without making any changes on the F5 device -- GET-only, no writes, safe to
run anytime.

Action Dependencies: requests

Inputs: host, partition (optional, default "Common"), verify_tls (optional),
virtualServers (list of {"name": "<fullPath>"} or plain fullPath strings --
vRA passes back whatever create/update last wrote into the resource's
properties). Credentials: "f5_username" and "F5_SHARED_PASSWORD" are bound
as Default Inputs on this action (String type for the password).

Output: {"virtualServers": [{"name", "destination", "enabled"}, ...],
"missing": [<name>, ...]}
"""

import os
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SHARED_SECRET_KEY = "F5_SHARED_PASSWORD"


def _resolve_credentials(inputs, host):
    username = inputs.get("f5_username") or inputs.get("username")
    password = inputs.get(SHARED_SECRET_KEY) or inputs.get("password")

    if not username or not password:
        raise RuntimeError(
            "F5 credentials missing for host {}: username={}, password={}".format(
                host, "set" if username else "MISSING", "set" if password else "MISSING"
            )
        )
    return username, password


def handler(context, inputs):
    host = inputs["host"]
    if isinstance(host, list):
        host = host[0] if host else ""
    if isinstance(host, dict):
        host = host.get("value", "")
    host = str(host).rstrip("/")

    username, password = _resolve_credentials(inputs, host)
    partition = inputs.get("partition") or "Common"
    verify_tls = bool(inputs.get("verify_tls", False))

    session = requests.Session()
    session.trust_env = False
    session.proxies = {}
    session.verify = verify_tls
    session.auth = (username, password)

    os.environ["NO_PROXY"] = "*"

    existing = inputs.get("virtualServers") or []
    refreshed = []
    missing = []

    for vs in existing:
        name = vs.get("name") if isinstance(vs, dict) else vs
        if not name:
            continue
        short_name = name.split("~")[-1] if "~" in name else name.split("/")[-1]

        url = "https://{}/mgmt/tm/ltm/virtual/~{}~{}".format(
            host, partition, short_name
        )

        try:
            resp = session.get(url, timeout=15)
        except requests.exceptions.RequestException as e:
            missing.append(short_name)
            continue

        if resp.status_code == 200:
            item = resp.json()
            refreshed.append({
                "name": item.get("fullPath", "/{}/{}".format(partition, short_name)),
                "destination": item.get("destination"),
                "enabled": not item.get("disabled", False),
            })
        elif resp.status_code == 404:
            missing.append(short_name)
        else:
            # Non-fatal: report as missing rather than crashing the read
            missing.append(short_name)

    result = dict(inputs)
    result["virtualServers"] = refreshed
    if missing:
        result["missing"] = missing
    return result
