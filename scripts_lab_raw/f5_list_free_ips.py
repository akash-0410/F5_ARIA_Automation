"""
ABX Action: f5_list_free_ips
--------------------------------
Custom Form data source for the "Virtual IP Address" field (VIP
Configuration section). Lets a user either type an IP address manually or
pick one from a live-computed list of free addresses within the F5
cluster's configured VIP subnet. This action's "options" are suggestions,
not a closed list -- the Custom Form field is a Combobox, so free typing
still works for addresses outside the configured subnet.

"Free" is computed as: every host address in the cluster's configured
CIDR, MINUS the network/broadcast addresses, MINUS any statically
reserved addresses (gateway, management IP, etc.), MINUS every address
already in use on the live F5 device as either an existing virtual
address (ltm/virtual-address) or an existing node address (ltm/node) --
so a freshly-picked IP won't collide with a running VIP or a backend
server.

Devices are matched to their VIP subnet WITHOUT CODE via the org's Action
Constants page (Extensibility > Actions > Action Constants >
F5_VIP_SUBNET_REGISTRY) -- edit that JSON value directly in the vRA UI to
add/change a cluster's VIP subnet; no changes to this script are needed.

F5_VIP_SUBNET_REGISTRY JSON shape:
{
  "<host value from F5 Cluster dropdown, e.g. 172.16.1.206>": {
    "cidr": "<VIP subnet CIDR, e.g. 172.16.1.0/24>",
    "reserved": ["<ip>", ...]   // optional: extra addresses to exclude
                                 // besides the network/broadcast
                                 // addresses, which are always excluded
  },
  ...
}

Inputs: host (bound to the F5 Cluster dropdown), verify_tls (optional).
Credentials: "f5_username" and "F5_SHARED_PASSWORD" are bound as Default
Inputs on this action (String type for the password), same convention as
the other live-query actions in this project.
Action Default Inputs required: f5_username (Default), F5_SHARED_PASSWORD
(Default), F5_VIP_SUBNET_REGISTRY (Type = Action constant, bound to the
F5_VIP_SUBNET_REGISTRY action constant).

Output: {"options": [{"label": "<ip>", "value": "<ip>"}, ...]}
List is capped at MAX_RESULTS and sorted in address order. If the live F5
device can't be reached, the action still returns the subnet's free
addresses computed from the registry alone (minus "reserved"), with an
"_error" key noting that in-use addresses could not be verified.
"""

import ipaddress
import json

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SHARED_SECRET_KEY = "F5_SHARED_PASSWORD"
MAX_RESULTS = 50


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


def _load_subnet_entry(inputs, host):
    raw_registry = inputs.get("F5_VIP_SUBNET_REGISTRY")
    if isinstance(raw_registry, dict):
        registry = raw_registry
    else:
        registry = json.loads(raw_registry or "{}")

    entry = registry.get(host)
    if not entry or not entry.get("cidr"):
        raise RuntimeError(
            "No VIP subnet configured for F5 host {}. Add an entry to the "
            "F5_VIP_SUBNET_REGISTRY action constant (Extensibility > Actions > "
            "Action Constants) for this host before requesting a free IP.".format(host)
        )
    return entry


def _used_addresses(session, host):
    used = set()
    any_success = False
    for resource in ("ltm/virtual-address", "ltm/node"):
        url = "https://{}/mgmt/tm/{}".format(host, resource)
        try:
            resp = session.get(url, timeout=15)
        except requests.exceptions.RequestException:
            continue
        if resp.status_code == 200:
            any_success = True
            for item in resp.json().get("items", []):
                addr = item.get("address") or item.get("name")
                if addr:
                    used.add(addr.split("%")[0].split("/")[0])
    return used, any_success


def handler(context, inputs):
    host = (inputs.get("host") or "").rstrip("/")
    if not host:
        raise RuntimeError("Missing required input 'host'")

    username, password = _resolve_credentials(inputs, host)
    verify_tls = bool(inputs.get("verify_tls", False))

    entry = _load_subnet_entry(inputs, host)
    network = ipaddress.ip_network(entry["cidr"], strict=False)
    reserved = set(entry.get("reserved") or [])

    session = requests.Session()
    session.verify = verify_tls
    session.auth = (username, password)

    used, any_success = _used_addresses(session, host)
    used |= reserved

    options = []
    for addr in network.hosts():
        addr_str = str(addr)
        if addr_str in used:
            continue
        options.append({"label": addr_str, "value": addr_str})
        if len(options) >= MAX_RESULTS:
            break

    result = {"options": options}
    if not any_success:
        result["_error"] = (
            "Could not reach F5 {} to check in-use addresses; list reflects the "
            "configured subnet only and may include addresses already in use.".format(host)
        )
    return result
