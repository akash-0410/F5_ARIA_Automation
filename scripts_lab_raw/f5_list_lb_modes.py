"""
ABX Action: f5_list_lb_modes
------------------------------
Custom Form data source for the "Load Balancing Method" dropdown. Queries
the live F5 device for LB methods currently in use across existing pools,
plus a fallback static list if no pools exist. The selected "value" is
passed straight through as "pool.load_balancing_mode".

Action Dependencies: requests

Inputs: host, verify_tls (optional). In the Custom Form designer, bind
"host" to the F5 Cluster dropdown.
Credentials: "f5_username" and "F5_SHARED_PASSWORD" are bound as
Default Inputs on this action (String type for the password).

Output: {"options": [{"label": ..., "value": ...}, ...]}
"""

import os
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SHARED_SECRET_KEY = "F5_SHARED_PASSWORD"

# Full known list as fallback when no pools exist on the device
ALL_LB_MODES = [
    "Round Robin",
    "Ratio (member)",
    "Least Connections (member)",
    "Observed (member)",
    "Predictive (member)",
    "Ratio (node)",
    "Least Connections (node)",
    "Fastest (node)",
    "Observed (node)",
    "Predictive (node)",
    "Dynamic Ratio (node)",
    "Fastest (application)",
    "Least Sessions",
    "Dynamic Ratio (member)",
    "Weighted Least Connections (member)",
    "Weighted Least Connections (node)",
    "Ratio (session)",
    "Ratio Least Connections (member)",
    "Ratio Least Connections (node)",
]

# Maps F5 API loadBalancingMode values to friendly names
LB_MODE_MAP = {
    "round-robin": "Round Robin",
    "ratio-member": "Ratio (member)",
    "least-connections-member": "Least Connections (member)",
    "observed-member": "Observed (member)",
    "predictive-member": "Predictive (member)",
    "ratio-node": "Ratio (node)",
    "least-connections-node": "Least Connections (node)",
    "fastest-node": "Fastest (node)",
    "observed-node": "Observed (node)",
    "predictive-node": "Predictive (node)",
    "dynamic-ratio-node": "Dynamic Ratio (node)",
    "fastest-application": "Fastest (application)",
    "least-sessions": "Least Sessions",
    "dynamic-ratio-member": "Dynamic Ratio (member)",
    "weighted-least-connections-member": "Weighted Least Connections (member)",
    "weighted-least-connections-node": "Weighted Least Connections (node)",
    "ratio-session": "Ratio (session)",
    "ratio-least-connections-member": "Ratio Least Connections (member)",
    "ratio-least-connections-node": "Ratio Least Connections (node)",
}


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
    verify_tls = bool(inputs.get("verify_tls", False))

    session = requests.Session()
    session.trust_env = False
    session.proxies = {}
    session.verify = verify_tls
    session.auth = (username, password)

    os.environ["NO_PROXY"] = "*"

    url = "https://{}/mgmt/tm/ltm/pool".format(host)

    try:
        resp = session.get(url, timeout=15)
    except requests.exceptions.RequestException:
        # Network error — return full static list
        return {
            "options": [{"label": m, "value": m} for m in ALL_LB_MODES],
            "_error": "Could not reach F5 at {}, returning full LB mode list".format(host),
        }

    if resp.status_code == 200:
        items = resp.json().get("items", [])
        if items:
            # Extract unique LB methods from existing pools
            seen = []
            for item in items:
                api_mode = item.get("loadBalancingMode", "")
                friendly = LB_MODE_MAP.get(api_mode, api_mode)
                if friendly not in seen:
                    seen.append(friendly)
            # Always include common defaults at the top
            for default in ["Round Robin", "Least Connections (member)", "Ratio (member)"]:
                if default not in seen:
                    seen.insert(0, default)
            return {"options": [{"label": m, "value": m} for m in seen]}

    # No pools found or non-200 — return full static list
    return {"options": [{"label": m, "value": m} for m in ALL_LB_MODES]}
