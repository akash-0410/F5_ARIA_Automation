"""
ABX Action: f5_list_nodes_grid
-------------------------------
Custom Form data source for the "Backend Nodes" Data Grid field's Default
value (External source) binding. Queries the live F5 device for existing
nodes in a partition and returns them as grid ROWS (one dict per row, keyed
to match the grid's column IDs: name, port, address, create_if_missing) --
NOT the {label, value} shape used by simple dropdown/search fields (that
shape is what f5_list_nodes still returns, unchanged, for anything else
that relies on it).

Existing nodes don't carry a port at the node level in F5 (port is a
pool-member property, set per-VS), so "port" comes back blank/null for
each row and the user fills it in on the form. "create_if_missing" comes
back False for every row returned here, since by definition these nodes
already exist on the device.

Credentials are NOT taken from the Custom Form: "f5_username" and the
shared password Secret are bound as Default Inputs on this action instead,
so end users never see or supply them (same pattern as every other F5
list-* action in this project).

Inputs:
    host        (string, required)  F5 device/cluster host, e.g. from the
                                     "F5 Cluster" form field.
    partition   (string, optional)  Defaults to "Common".
    f5_username (string, Default Input)
    F5_SHARED_PASSWORD (string, Default Input, secret)
    verify_tls  (bool, optional)    Defaults to False.

Output:
    {"nodes": [{"name": "/Common/juice_shop", "port": None,
                "address": "10.10.1.3", "create_if_missing": False}, ...]}
"""
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
    host = inputs["host"].rstrip("/")
    username, password = _resolve_credentials(inputs, host)
    partition = inputs.get("partition") or "Common"
    verify_tls = bool(inputs.get("verify_tls", False))

    session = requests.Session()
    session.verify = verify_tls
    session.auth = (username, password)

    resp = session.get(f"https://{host}/mgmt/tm/ltm/node")

    nodes = []
    if resp.status_code == 200:
        for item in resp.json().get("items", []):
            if partition == "Common" or item.get("partition") == partition:
                full_path = item.get("fullPath", item.get("name"))
                address = item.get("address", "N/A")
                nodes.append({
                    "name": full_path,
                    "port": None,
                    "address": address,
                    "create_if_missing": False,
                })
    else:
        raise RuntimeError(f"Failed to list nodes from {host}: {resp.status_code} {resp.text}")

    return {"nodes": nodes}
