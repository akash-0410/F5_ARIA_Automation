"""
ABX Action: f5_update_pool_settings
--------------------------------------
Day-2 targeted update: reconciles ONLY the Health Monitor Type and Load
Balancing Method on an EXISTING F5 pool. Does not touch the pool's nodes,
the virtual server, VIP address, or any other F5.VirtualServer property --
use this instead of re-running f5_create_virtual_server for these two
fields, so unrelated already-provisioned resources (VS, VIP, existing pool
members) are never re-evaluated and can't trip an "already exists" error.

Inputs:
    host, partition, verify_tls
    pool_name             -- the pool's short name (no partition prefix)
    monitor_type          -- exact monitor path from f5_list_monitors, or
                              "" / omitted to clear the pool's monitor
    load_balancing_mode   -- exact mode string from f5_list_lb_modes

Credentials: same pattern as f5_create_virtual_server -- "f5_username" and
F5_SHARED_PASSWORD are bound as Action Default Inputs, never supplied by
the requester.

NOTE: clearing an existing monitor is implemented as PATCH {"monitor": ""}.
This matches common iControl REST convention but has not been exercised
against this environment's specific BIG-IP version -- verify once against
a test pool before relying on it to remove a monitor that was previously
set.

Output:
    { "poolName": "/<partition>/<pool_name>" }
"""

import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

SHARED_SECRET_KEY = "F5_SHARED_PASSWORD"


class F5OperationError(RuntimeError):
    pass


def _resolve_credentials(inputs, host):
    username = inputs.get("f5_username") or inputs.get("username")
    password = inputs.get(SHARED_SECRET_KEY) or inputs.get("password")

    if not username or not password:
        raise RuntimeError(
            "F5 credentials missing for {}: username={}, password={}".format(
                host, "set" if username else "MISSING", "set" if password else "MISSING"
            )
        )
    return username, password


class F5Manager:
    def __init__(self, host, username, password, partition="Common", verify_tls=False):
        self.host = host.rstrip("/")
        self.partition = partition
        self.base_url = f"https://{self.host}/mgmt/tm"
        self.session = requests.Session()
        self.session.verify = verify_tls
        self.session.auth = (username, password)
        self.session.headers.update({"Content-Type": "application/json"})

    def _get(self, uri):
        return self.session.get(f"{self.base_url}{uri}")

    def _patch(self, uri, payload):
        return self.session.patch(f"{self.base_url}{uri}", json=payload)

    @staticmethod
    def _ok(resp):
        return resp.status_code in (200, 201, 202)

    def update_pool_settings(self, pool_name, monitor_name=None, load_balancing_mode=None):
        pool_fqdn = f"/{self.partition}/{pool_name}"
        resp = self._get(f"/ltm/pool/~{self.partition}~{pool_name}")
        if resp.status_code != 200:
            raise F5OperationError(
                f"Pool '{pool_fqdn}' not found on {self.host} -- it must already exist. "
                f"This action only updates an existing pool's monitor / load-balancing method."
            )
        existing = resp.json()
        changes = {}

        if load_balancing_mode and existing.get("loadBalancingMode") != load_balancing_mode:
            changes["loadBalancingMode"] = load_balancing_mode

        existing_monitor = (existing.get("monitor") or "").strip()
        desired_monitor = (monitor_name or "").strip()
        # existing_monitor comes back from BIG-IP looking like " /Common/http " or "" -- compare loosely
        if desired_monitor != existing_monitor:
            changes["monitor"] = desired_monitor

        if not changes:
            return pool_fqdn

        patch_resp = self._patch(f"/ltm/pool/~{self.partition}~{pool_name}", changes)
        if not self._ok(patch_resp):
            raise F5OperationError(f"Failed to update pool '{pool_fqdn}': {patch_resp.text}")
        return pool_fqdn


def handler(context, inputs):
    host = inputs["host"]
    username, password = _resolve_credentials(inputs, host)
    partition = inputs.get("partition") or "Common"
    verify_tls = bool(inputs.get("verify_tls", False))

    pool_name = inputs["pool_name"]
    monitor_type = inputs.get("monitor_type") or ""
    load_balancing_mode = inputs.get("load_balancing_mode") or "round-robin"

    f5 = F5Manager(host, username, password, partition, verify_tls=verify_tls)
    pool_fqdn = f5.update_pool_settings(
        pool_name, monitor_name=monitor_type, load_balancing_mode=load_balancing_mode
    )

    return {"poolName": pool_fqdn}
