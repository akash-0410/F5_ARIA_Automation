"""
ABX Action: f5_list_monitors
------------------------------
Custom Form data source for the "Health Monitor" dropdown -- lists EXISTING
health monitors already configured on the target F5 device (F5's built-in
monitors like /Common/tcp and /Common/https, plus any custom monitors an
admin has already created there), so a request can attach to one directly.

No monitor is ever created or modified by this action, or by anything that
consumes its output -- f5_create_virtual_server just uses the selected
monitor path as-is. Replaces f5_list_monitor_types for this purpose (that
action listed monitor TYPE categories for creating a new monitor, which we
no longer do).

Inputs:
    host        (string, required)  F5 device/cluster host, from the
                                     "F5 Cluster" form field.
    partition   (string, optional)  Defaults to "Common". Monitors in this
                                     partition and in /Common are returned
                                     (pools can reference /Common objects
                                     from any partition).
    f5_username (string, Default Input)
    F5_SHARED_PASSWORD (string, Default Input, secret)
    verify_tls  (bool, optional)    Defaults to False.

Output:
    {"options": [{"label": "tcp (Common)", "value": "/Common/tcp"}, ...]}
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


def _monitor_types(session, host):
    resp = session.get("https://{}/mgmt/tm/ltm/monitor".format(host), timeout=15)
    resp.raise_for_status()
    types = []
    for item in resp.json().get("items", []):
        link = item.get("selfLink") or (item.get("reference") or {}).get("link", "")
        match = re.search(r"/ltm/monitor/([^/?]+)", link)
        if match:
            types.append(match.group(1))
    return types


def handler(context, inputs):
    host = inputs.get("host")
    if isinstance(host, list):
        host = host[0] if host else ""
    if isinstance(host, dict):
        host = host.get("value", "")
    host = str(host or "").rstrip("/")
    if not host:
        raise RuntimeError("Missing required input 'host'")

    partition = inputs.get("partition") or "Common"
    username, password = _resolve_credentials(inputs, host)
    verify_tls = bool(inputs.get("verify_tls", False))

    session = requests.Session()
    session.verify = verify_tls
    session.auth = (username, password)

    options = [{"label": "None (skip health monitoring)", "value": ""}]
    seen = set()
    for mon_type in _monitor_types(session, host):
        resp = session.get("https://{}/mgmt/tm/ltm/monitor/{}".format(host, mon_type), timeout=15)
        if resp.status_code != 200:
            continue
        for item in resp.json().get("items", []):
            item_partition = item.get("partition", "Common")
            if item_partition not in ("Common", partition):
                continue
            full_path = item.get("fullPath", "/{}/{}".format(item_partition, item.get("name")))
            if full_path in seen:
                continue
            seen.add(full_path)
            options.append({
                "label": "{} ({}, {})".format(item.get("name"), mon_type, item_partition),
                "value": full_path,
            })

    options[1:] = sorted(options[1:], key=lambda o: o["label"])
    return {"options": options}
