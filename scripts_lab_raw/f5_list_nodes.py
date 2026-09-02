"""
ABX Action: f5_list_nodes
----------------------------
Custom Form data source for the backend-node search/select field. Queries
the live F5 device for existing nodes in a partition.

Action Dependencies: requests

Inputs: host, partition (optional, default "Common"), verify_tls (optional).
In the Custom Form designer, bind "host" to the F5 Cluster dropdown.
Credentials are NOT taken from the Custom Form: "f5_username" and a
per-cluster password Secret (see F5_CREDENTIAL_MAP) are bound as Default
Inputs on this action instead, so end users never see or supply them.
Action Default Inputs required: f5_username (Default), plus one Secret-type
Default Input per F5_CREDENTIAL_MAP entry (Name = the Secret's name, e.g.
F5_LOCATION1_PASSWORD / F5_LOCATION2_PASSWORD).

Output: {"options": [{"label": "<name> (<address>)", "value": "<fullPath>"}, ...]}
"""

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Maps an F5 cluster's management host (the "F5 Cluster" dropdown's value,
# from f5_list_clusters) to the name of the vRA Secret holding that
# device's password. Add an entry here -- and a matching Secret-type
# Default Input on this action -- whenever a new F5 cluster is onboarded.
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
    host = inputs["host"].rstrip("/")
    username, password = _resolve_credentials(inputs, host)
    partition = inputs.get("partition") or "Common"
    verify_tls = bool(inputs.get("verify_tls", False))

    session = requests.Session()
    session.verify = verify_tls
    session.auth = (username, password)

    resp = session.get(f"https://{host}/mgmt/tm/ltm/node")
    options = []
    if resp.status_code == 200:
        for item in resp.json().get("items", []):
            if partition == "Common" or item.get("partition") == partition:
                full_path = item.get("fullPath", item.get("name"))
                address = item.get("address", "N/A")
                options.append({"label": f"{full_path} ({address})", "value": full_path})
    else:
        raise RuntimeError(f"Failed to list nodes from {host}: {resp.status_code} {resp.text}")

    return {"options": options}
