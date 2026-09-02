"""
ABX Action: f5_list_snat_pools
---------------------------------
Custom Form data source for the "Source Address Translation (SNAT)"
dropdown (VIP Configuration section of the requirements doc). Always
offers the two built-in SNAT modes (Automap / None) plus any real SNAT
pools defined on the live F5 device. The selected "value" is passed
straight through as "vs.snat" -- the create action already understands
"automap", "none", or a SNAT pool fullPath (see F5Manager.create_virtual_server).

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

def _coerce_scalar(value, name):
    """Defensive net: some vRO wrapper actions have their input params
    mistyped as Array (a config error, not intended behavior). If that
    happens, this input arrives here as a JSON list instead of a string.
    Unwrap a clean single-element list; raise loudly on anything else so
    the underlying vRO misconfiguration gets fixed, not silently masked."""
    if isinstance(value, list):
        if len(value) != 1:
            raise RuntimeError(
                "Input '{}' arrived as a {}-element list ({!r}); expected a scalar. "
                "Check vRO action input typing (Array checkbox likely set) "
                "on the wrapper for this action.".format(name, len(value), value)
            )
        print("WARNING: input '{}' arrived as a 1-element list; coercing to scalar. "
              "Fix the vRO wrapper's input typing.".format(name))
        return value[0]
    return value


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
    host = _coerce_scalar(inputs.get("host"), "host")
    if not host:
        raise RuntimeError("Missing required input 'host'")
    host = host.rstrip("/")
    username, password = _resolve_credentials(inputs, host)
    verify_tls = bool(inputs.get("verify_tls", False))

    session = requests.Session()
    session.trust_env = False
    session.proxies = {}
    session.verify = verify_tls
    session.auth = (username, password)

    os.environ["NO_PROXY"] = "*"

    options = [
        {"label": "Automap", "value": "automap"},
        {"label": "None", "value": "none"},
    ]

    url = "https://{}/mgmt/tm/ltm/snatpool".format(host)

    try:
        resp = session.get(url, timeout=15)
    except requests.exceptions.RequestException as e:
        return {
            "options": options,
            "_error": "Failed to reach F5 at {}: {}".format(host, e),
        }

    if resp.status_code == 200:
        for item in resp.json().get("items", []):
            full_path = item.get("fullPath", item.get("name"))
            if full_path:
                options.append({"label": full_path, "value": full_path})

    return {"options": options}
