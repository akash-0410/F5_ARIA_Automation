"""
ABX Action: f5_list_monitor_types
----------------------------------
Custom Form data source for the "Health Monitor Type" dropdown (used when
creating a NEW health monitor for a pool). Queries the live F5 device for
the monitor TYPES it actually supports via GET /mgmt/tm/ltm/monitor --
this endpoint returns the type collections available on that device
(varies by license/module), not individual monitor instances.

The selected "value" is a plain type name (e.g. "https"), passed straight
through as "pool.monitor_type" and used by f5_create_virtual_server to
POST a NEW monitor of that type. It is NOT a path to an existing monitor
object -- that's a separate concept (see the "Health Monitor" field /
f5_list_monitors action, for picking an EXISTING monitor to attach).

Inputs: host (bind to F5 Cluster dropdown), verify_tls (optional).
Credentials: "f5_username" and "F5_SHARED_PASSWORD" are bound as Default
Inputs on this action.

Output: {"options": [{"label": "<type>", "value": "<type>"}, ...]}
"""

import re
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


def _extract_type(item):
    # Prefer the collection's own link -- ".../ltm/monitor/https?ver=..."
    link = item.get("selfLink") or (item.get("reference") or {}).get("link", "")
    match = re.search(r"/ltm/monitor/([^/?]+)", link)
    if match:
        return match.group(1)
    # Fall back to "kind", e.g. "tm:ltm:monitor:https:httpscollectionstate"
    parts = item.get("kind", "").split(":")
    return parts[3] if len(parts) >= 4 else None


def handler(context, inputs):
    host = inputs.get("host")
    if isinstance(host, list):
        host = host[0] if host else ""
    if isinstance(host, dict):
        host = host.get("value", "")
    host = str(host or "").rstrip("/")
    if not host:
        raise RuntimeError("Missing required input 'host'")

    username, password = _resolve_credentials(inputs, host)
    verify_tls = bool(inputs.get("verify_tls", False))

    session = requests.Session()
    session.verify = verify_tls
    session.auth = (username, password)

    resp = session.get("https://{}/mgmt/tm/ltm/monitor".format(host), timeout=15)
    resp.raise_for_status()

    options = [{"label": "None (skip health monitoring)", "value": ""}]
    seen = set()
    for item in resp.json().get("items", []):
        mon_type = _extract_type(item)
        if mon_type and mon_type not in seen:
            seen.add(mon_type)
            options.append({"label": mon_type, "value": mon_type})

    options[1:] = sorted(options[1:], key=lambda o: o["label"])
    return {"options": options}
