"""
ABX Action: f5_update_backend_nodes
--------------------------------------
Day-2 targeted update: reconciles ONLY an existing pool's node membership
to match the requester's edited Backend Nodes list. Reads the pool's
CURRENT members directly from BIG-IP and diffs against the submitted
list -- it never re-runs the full f5_create_virtual_server create/
reconcile flow, so the virtual server, VIP address, monitor, and
load-balancing method are never re-evaluated and can't be accidentally
reset or throw on already-existing state.

Inputs:
    host, partition, verify_tls
    pool_name  -- the pool's short name (no partition prefix)
    nodes: [ { name, address, port, create_if_missing } ]  -- the FULL
        desired Backend Nodes list from the Day-2 form (not a diff --
        this action computes the diff itself against BIG-IP's live state,
        so a row simply omitted from this list is treated as "remove it").

Credentials: same pattern as f5_create_virtual_server -- "f5_username" and
F5_SHARED_PASSWORD are bound as Action Default Inputs, never supplied by
the requester.

Output:
    {
      "added":     [ "<node_full_path>:<port>", ... ],
      "removed":   [ "<node_full_path>:<port>", ... ],
      "unchanged": [ "<node_full_path>:<port>", ... ]
    }
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

    def _post(self, uri, payload):
        return self.session.post(f"{self.base_url}{uri}", json=payload)

    def _delete(self, uri):
        return self.session.delete(f"{self.base_url}{uri}")

    @staticmethod
    def _ok(resp):
        return resp.status_code in (200, 201, 202)

    def list_pool_members(self, pool_name):
        resp = self._get(f"/ltm/pool/~{self.partition}~{pool_name}/members")
        if resp.status_code != 200:
            raise F5OperationError(
                f"Pool '/{self.partition}/{pool_name}' not found on {self.host} -- it must "
                f"already exist. This action only updates an existing pool's membership."
            )
        members = {}
        for item in resp.json().get("items", []):
            full_path = item.get("fullPath") or item.get("name")
            members[full_path] = item
        return members

    def create_node(self, name, address):
        node_fqdn = f"/{self.partition}/{name}"
        resp = self._get(f"/ltm/node/~{self.partition}~{name}")
        if resp.status_code == 200:
            existing_address = resp.json().get("address")
            if address and existing_address and existing_address != address:
                raise F5OperationError(
                    f"Node '{node_fqdn}' already exists with address '{existing_address}', "
                    f"which differs from requested '{address}'. Node addresses are immutable "
                    f"on BIG-IP -- delete and recreate manually if this needs to change."
                )
            return node_fqdn
        payload = {"name": name, "partition": self.partition, "address": address}
        resp = self._post("/ltm/node", payload)
        if not self._ok(resp):
            raise F5OperationError(f"Failed to create node '{node_fqdn}': {resp.text}")
        return node_fqdn

    def add_pool_member(self, pool_name, node_full_path, port):
        member_name = f"{node_full_path}:{port}"
        payload = {"name": member_name, "partition": self.partition}
        resp = self._post(f"/ltm/pool/~{self.partition}~{pool_name}/members", payload)
        if self._ok(resp):
            return
        if resp.status_code == 400 and "already exists" in (resp.text or "").lower():
            return
        raise F5OperationError(
            f"Failed to add member '{member_name}' to pool '/{self.partition}/{pool_name}': {resp.text}"
        )

    def remove_pool_member(self, pool_name, member_full_path):
        # e.g. "/Common/web01:8080" -> "~Common~web01:8080"
        short = member_full_path[1:].replace("/", "~", 1) if member_full_path.startswith("/") else member_full_path
        resp = self._delete(f"/ltm/pool/~{self.partition}~{pool_name}/members/~{short}")
        if self._ok(resp) or resp.status_code == 404:
            return
        raise F5OperationError(
            f"Failed to remove member '{member_full_path}' from pool '/{self.partition}/{pool_name}': {resp.text}"
        )


def handler(context, inputs):
    host = inputs["host"]
    username, password = _resolve_credentials(inputs, host)
    partition = inputs.get("partition") or "Common"
    verify_tls = bool(inputs.get("verify_tls", False))
    pool_name = inputs["pool_name"]
    nodes = inputs.get("nodes", [])

    f5 = F5Manager(host, username, password, partition, verify_tls=verify_tls)

    desired = {}
    for n in nodes:
        node_name = n.get("name")
        address = n.get("address")
        raw_port = n.get("port")
        if not node_name:
            raise F5OperationError("Each Backend Nodes row must include a Node Name.")
        if raw_port in (None, "", "null"):
            raise F5OperationError(f"Backend node '{node_name}' is missing a Port.")
        port = str(raw_port)
        create_if_missing = bool(n.get("create_if_missing", False))
        node_full_path = node_name if node_name.startswith("/") else f"/{partition}/{node_name}"
        member_full_path = f"{node_full_path}:{port}"
        desired[member_full_path] = {
            "node_full_path": node_full_path,
            "short_name": node_name.split("/", 2)[-1] if node_name.startswith("/") else node_name,
            "address": address,
            "port": port,
            "create_if_missing": create_if_missing,
        }

    existing = f5.list_pool_members(pool_name)

    added, removed, unchanged = [], [], []

    for member_full_path, meta in desired.items():
        if member_full_path in existing:
            unchanged.append(member_full_path)
            continue
        if meta["address"] and meta["create_if_missing"]:
            f5.create_node(meta["short_name"], meta["address"])
        f5.add_pool_member(pool_name, meta["node_full_path"], meta["port"])
        added.append(member_full_path)

    for member_full_path in existing:
        if member_full_path not in desired:
            f5.remove_pool_member(pool_name, member_full_path)
            removed.append(member_full_path)

    return {"added": added, "removed": removed, "unchanged": unchanged}
