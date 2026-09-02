"""
ABX Action: f5_delete_virtual_server
--------------------------------------
Day-2 delete entry point for the F5.VirtualServer custom resource.

By design this ONLY removes the virtual server object(s) created for this
deployment. It deliberately leaves the pool, pool members, and nodes in
place, since those may be shared with other virtual servers/deployments
that this custom resource doesn't know about -- deleting them here could
silently break an unrelated VS. If a full teardown (pool + members +
orphaned nodes) is wanted, that needs to be a separate, explicitly-invoked
Day-2 action ("Purge pool"), not the default delete path.

Action Dependencies: requests

Inputs: "host"/"partition"/"verify_tls" as the create action, plus
"virtualServers": [ "/Common/vs-name-80", ... ] -- normally passed straight
through from the create action's recorded outputs on the resource.
Credentials: "f5_username" and "F5_SHARED_PASSWORD" are bound as
Default Inputs on this action (String type for the password).

Output: {"deleted": ["/Common/vs-name-80", ...]}
"""

import os
import json
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
    virtual_servers = inputs.get("virtualServers", [])

    session = requests.Session()
    session.trust_env = False
    session.proxies = {}
    session.verify = verify_tls
    session.auth = (username, password)

    os.environ["NO_PROXY"] = "*"

    base_url = "https://{}/mgmt/tm".format(host)

    deleted = []
    failed = []

    for vs_entry in virtual_servers:
        # Handle both plain paths and JSON-serialized objects
        if isinstance(vs_entry, dict):
            vs_name = vs_entry.get("name", "")
        elif isinstance(vs_entry, str):
            try:
                parsed = json.loads(vs_entry)
                if isinstance(parsed, dict):
                    vs_name = parsed.get("name", "")
                else:
                    vs_name = parsed
            except (ValueError, TypeError):
                vs_name = vs_entry
        else:
            continue

        if not vs_name:
            continue

        # Extract partition and short name from full path
        # e.g. "/Common/test-vra-vs01" -> partition="Common", name="test-vra-vs01"
        parts = vs_name.strip("/").split("/", 1)
        if len(parts) == 2:
            vs_partition, short_name = parts[0], parts[1]
        else:
            vs_partition, short_name = partition, parts[0]

        url = "{}/ltm/virtual/~{}~{}".format(base_url, vs_partition, short_name)

        try:
            resp = session.delete(url, timeout=15)
        except requests.exceptions.RequestException as e:
            failed.append({"vs": vs_name, "status": "error", "detail": str(e)})
            continue

        if resp.status_code in (200, 204, 404):
            deleted.append(vs_name)
        else:
            failed.append({
                "vs": vs_name,
                "status": resp.status_code,
                "detail": resp.text,
            })

    if failed:
        raise RuntimeError(
            "Failed to delete {} virtual server(s): {}".format(len(failed), failed)
        )

    return {"deleted": deleted}
