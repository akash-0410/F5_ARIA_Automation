"""
ABX Action: f5_list_persistence_profiles
-------------------------------------------
Custom Form data source for the "Persistence Profile" dropdown. Queries
the live F5 device for existing persistence profiles, plus a "None"
option. The selected "value" is passed straight through as
"vs.persistence_profile".

Action Dependencies: requests

Inputs: host, partition (optional, default "Common"), verify_tls (optional).
In the Custom Form designer, bind "host" to the F5 Cluster dropdown.
Credentials: "f5_username" and "F5_SHARED_PASSWORD" are bound as
Default Inputs on this action (String type for the password).

Output: {"options": [{"label": "<fullPath> (<type>)", "value": "<fullPath>"}, ...]}
"""

import os
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SHARED_SECRET_KEY = "F5_SHARED_PASSWORD"

PERSISTENCE_TYPES = []


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

def _get_persistence_types(session, host, verify_tls):
    """Query the F5 for available persistence type subcollections."""
    url = "https://{}/mgmt/tm/ltm/persistence".format(host)
    try:
        resp = session.get(url, timeout=15)
        if resp.status_code == 200:
            types = []
            for item in resp.json().get("items", []):
                link = item.get("reference", {}).get("link", "")
                # Extract type name from URL like
                # "https://localhost/mgmt/tm/ltm/persistence/cookie?ver=17.5.0"
                if "/ltm/persistence/" in link:
                    ptype = link.split("/ltm/persistence/")[1].split("?")[0]
                    if ptype != "global-settings":
                        types.append(ptype)
            return types
    except Exception:
        pass
    return ["cookie", "source-addr", "ssl", "universal", "hash"]

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

    options = [{"label": "None", "value": ""}]

    # Discover persistence types from the F5 device
    ptypes = _get_persistence_types(session, host, verify_tls)

    for ptype in ptypes:
        url = "https://{}/mgmt/tm/ltm/persistence/{}".format(host, ptype)

        try:
            resp = session.get(url, timeout=15)
        except requests.exceptions.RequestException:
            continue

        if resp.status_code != 200:
            continue

        for item in resp.json().get("items", []):
            if partition != "Common" and item.get("partition") != partition:
                continue
            full_path = item.get("fullPath", item.get("name"))
            if full_path:
                label_type = ptype.replace("-", " ").title()
                options.append({
                    "label": "{} ({})".format(full_path, label_type),
                    "value": full_path,
                })

    return {"options": options}
