"""
ABX Action: f5_create_virtual_server
-------------------------------------
Create/Day-2-update entry point for the F5.VirtualServer custom resource.
Ported from f5_manager.py + non_interactive_orchestrator.py into a single
self-contained file (ABX actions run in an isolated FaaS sandbox with no
access to the rest of the automation repo, so this has no local imports).

Action Dependencies (set in the vRA Action editor "Dependencies" field):
    requests

Inputs (from the Custom Resource's create/update payload -- see the
F5.VirtualServer custom resource schema / the Cloud Template inputs):
    host, partition, verify_tls
    vs: { name, destination_ip, port | ports[], type, protocol, snat,
          oneconnect_profile, persistence_profile }
    pool: { name, load_balancing_mode, monitor, monitor_type,
            monitor_interval, monitor_timeout }
    nodes: [ { name, address, port, create_if_missing } ]

Credentials are NOT taken from the Custom Form: "f5_username" (Default
Input) and "F5_SHARED_PASSWORD" (Secret Input) are bound as Default/Secret
Inputs on this action instead, so end users never see or supply them.
NOTE: this is currently ONE shared username/password pair used for EVERY
F5 host this action talks to -- there is no per-host/per-cluster credential
map today, despite the SHARED_SECRET_KEY constant name below suggesting
otherwise. See the SOP's Known Risks section (credential model) before
assuming multiple F5 clusters with different passwords are supported as-is.
Action Default Inputs required: f5_username (Default), F5_SHARED_PASSWORD
(Secret).

If vs.destination_ip is omitted (or set to "auto"), a free IP is picked
automatically from that host's configured subnet, keyed by host in the
F5_VIP_SUBNET_REGISTRY Action Constant (JSON) -- the requester never
supplies or sees a VIP address. "Available" means:
not already assigned to any ltm virtual-address on the device, not one of
the device's own self IPs, and not the management host IP itself.

Outputs:
    virtualServers: [ "/<partition>/<vs_name>", ... ] if only one port was
        requested, otherwise [ "/<partition>/<vs_name>-<port>", ... ] (the
        port suffix is only added when vs.ports has more than one entry).
    poolName, destinationIp
"""

import ipaddress
import json
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Name of the single Secret Input holding the F5 API password used for
# EVERY host this action talks to. There is currently no per-cluster
# credential map -- onboarding a new F5 host that needs a *different*
# password is not supported without a code change (see SOP Known Risks,
# item 1). Rotating the one shared password is a plain overwrite of this
# Secret Input's value.
SHARED_SECRET_KEY = "F5_SHARED_PASSWORD"

# F5_VIP_SUBNET_REGISTRY (an Action Constant, JSON) maps each F5 host to
# its VIP subnet CIDR and any reserved addresses. Add an entry there --
# no code change required -- whenever a new F5 host is onboarded for VIP
# auto-assignment.
def _vip_subnet_entry(inputs, host):
    raw_registry = inputs.get("F5_VIP_SUBNET_REGISTRY")
    if isinstance(raw_registry, dict):
        registry = raw_registry
    else:
        try:
            registry = json.loads(raw_registry or "{}")
        except (TypeError, ValueError) as exc:
            raise F5OperationError(
                "F5_VIP_SUBNET_REGISTRY is not valid JSON ({}). Check the Action "
                "Constant configured on this ABX action.".format(exc)
            )
    return registry.get(host)


def _resolve_credentials(inputs, host):
    username = inputs.get("f5_username") or inputs.get("username")
    password = inputs.get(SHARED_SECRET_KEY) or inputs.get("password")

    if not username or not password:
        raise F5OperationError(
            "F5 credentials missing for host {}: username={}, password={}".format(
                host, "set" if username else "MISSING", "set" if password else "MISSING"
            )
        )
    return username, password

# ---------------------------------------------------------------------
# config (mirrors f5_automation/config.py)
# ---------------------------------------------------------------------
LB_MODE_MAP = {
    "Round Robin": "round-robin",
    "Ratio (member)": "ratio-member",
    "Least Connections (member)": "least-connections-member",
    "Observed (member)": "observed-member",
    "Predictive (member)": "predictive-member",
    "Ratio (node)": "ratio-node",
    "Least Connections (node)": "least-connections-node",
    "Fastest (node)": "fastest-node",
    "Observed (node)": "observed-node",
    "Predictive (node)": "predictive-node",
    "Dynamic Ratio (node)": "dynamic-ratio-node",
    "Fastest (application)": "fastest-app-response",
    "Least Sessions": "least-sessions",
    "Dynamic Ratio (member)": "dynamic-ratio-member",
    "Weighted Least Connections (member)": "weighted-least-connections-member",
    "Weighted Least Connections (node)": "weighted-least-connections-node",
    "Ratio (session)": "ratio-session",
    "Ratio Least Connections (member)": "ratio-least-connections-member",
    "Ratio Least Connections (node)": "ratio-least-connections-node",
}

PERSISTENCE_PROFILE_MAP = {
    "cookie": "/Common/cookie", "Cookie": "/Common/cookie",
    "source address": "/Common/source_addr", "Source Address": "/Common/source_addr",
    "ssl": "/Common/ssl", "SSL": "/Common/ssl",
    "universal": "/Common/universal", "Universal": "/Common/universal",
}

HTTP_CLASS_PROFILES = {"/Common/http", "/Common/https", "/Common/fasthttp"}
HTTP_REQUIRED_PERSISTENCE = {"/Common/cookie"}

DEFAULT_MONITOR_INTERVAL = 5
DEFAULT_MONITOR_TIMEOUT = 16


class F5OperationError(RuntimeError):
    pass


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

    def _patch(self, uri, payload):
        return self.session.patch(f"{self.base_url}{uri}", json=payload)

    @staticmethod
    def _ok(resp):
        return resp.status_code in (200, 201, 202)

    def list_profiles(self):
        profiles = {}
        for ptype in ("tcp", "udp", "http", "fastl4", "fasthttp", "clientssl",
                      "serverssl", "ipother", "l2forward", "dhcpv4", "oneconnect"):
            try:
                resp = self._get(f"/ltm/profile/{ptype}")
                if resp.status_code == 200:
                    for item in resp.json().get("items", []):
                        fp = item.get("fullPath", "")
                        if fp:
                            profiles[ptype] = fp
                            break
            except Exception:
                continue
        return profiles

    def next_available_ip(self, cidr, reserved=None):
        """Return the first address in `cidr` not already claimed on this
        device -- skips the device's own self IPs, the management host IP,
        any statically `reserved` addresses (e.g. gateway), and every
        address already used by an existing ltm virtual-address.
        Network/broadcast addresses are excluded automatically by
        ipaddress.hosts()."""
        network = ipaddress.ip_network(cidr, strict=False)
        used = {self.host} | set(reserved or [])

        try:
            resp = self._get("/net/self")
            if resp.status_code == 200:
                for item in resp.json().get("items", []):
                    addr = (item.get("address") or "").split("/")[0].split("%")[0]
                    if addr:
                        used.add(addr)
        except Exception:
            pass

        try:
            resp = self._get("/ltm/virtual-address")
            if resp.status_code == 200:
                for item in resp.json().get("items", []):
                    addr = (item.get("address") or "").split("/")[0].split("%")[0]
                    if addr:
                        used.add(addr)
        except Exception:
            pass

        for candidate in network.hosts():
            candidate_str = str(candidate)
            if candidate_str not in used:
                return candidate_str

        raise F5OperationError(f"No available IPs remaining in {cidr} on {self.host}.")

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

    def create_monitor(self, monitor_name, monitor_type, interval=None, timeout=None):
        """
        Health monitors are never created or modified here -- monitor_type is
        the exact monitor path already selected from the device's existing
        monitors (see f5_list_monitors) and is used as-is.
        """
        if not monitor_type:
            return None
        return monitor_type

    def create_pool(self, pool_name, monitor_name=None, load_balancing_mode="round-robin"):
        pool_fqdn = f"/{self.partition}/{pool_name}"
        resp = self._get(f"/ltm/pool/~{self.partition}~{pool_name}")
        if resp.status_code == 200:
            existing = resp.json()
            changes = {}
            if load_balancing_mode and existing.get("loadBalancingMode") != load_balancing_mode:
                changes["loadBalancingMode"] = load_balancing_mode
            existing_monitor = (existing.get("monitor") or "").strip()
            if monitor_name and existing_monitor != monitor_name:
                changes["monitor"] = monitor_name
            if changes:
                patch_resp = self._patch(f"/ltm/pool/~{self.partition}~{pool_name}", changes)
                if not self._ok(patch_resp):
                    raise F5OperationError(f"Failed to reconcile pool '{pool_fqdn}': {patch_resp.text}")
            return pool_fqdn
        payload = {"name": pool_name, "partition": self.partition, "loadBalancingMode": load_balancing_mode}
        if monitor_name:
            payload["monitor"] = monitor_name
        resp = self._post("/ltm/pool", payload)
        if not self._ok(resp):
            raise F5OperationError(f"Failed to create pool '{pool_fqdn}': {resp.text}")
        return pool_fqdn

    def add_pool_member(self, pool_name, node_full_path, port):
        member_name = f"{node_full_path}:{port}"
        payload = {"name": member_name, "partition": self.partition}
        resp = self._post(f"/ltm/pool/~{self.partition}~{pool_name}/members", payload)
        if self._ok(resp):
            return
        if resp.status_code == 400 and "already exists" in (resp.text or "").lower():
            return
        raise F5OperationError(f"Failed to add member '{member_name}' to pool '/{self.partition}/{pool_name}': {resp.text}")

    def create_virtual_server(self, vs_name, destination_ip, port, pool_name, vs_type="standard",
                               protocol=None, snat=None, oneconnect_profile=None,
                               persistence_profile=None, available_profiles=None):
        vs_fqdn = f"/{self.partition}/{vs_name}"
        destination = f"{destination_ip}:{port}"
        prof = available_profiles or {}
        no_pool_types = ("forwarding-ip", "forwarding-l2")
    
        # Fast L4 / forwarding virtual server types use a low-level, stateless
        # L4 fast-path profile and cannot be combined with full-proxy L7
        # profiles (HTTP, OneConnect) or with persistence types that need
        # HTTP-layer visibility (Cookie). F5 rejects the combination with
        # "01070095:3: ... lists incompatible profiles" -- fail early here
        # with a clear message instead of letting that opaque error surface.
        l4_only_types = ("performance-l4", "forwarding-l2", "forwarding-ip", "dhcp")
        if vs_type in l4_only_types:
            if oneconnect_profile:
                raise F5OperationError(
                    f"Virtual server type '{vs_type}' uses a Fast L4/forwarding profile and can't "
                    f"also use a OneConnect profile. Remove the OneConnect profile or change the "
                    f"Virtual Server Type to 'standard' or 'performance-http'."
                )
            if persistence_profile and persistence_profile != "none":
                resolved_check = PERSISTENCE_PROFILE_MAP.get(persistence_profile, persistence_profile)
                if resolved_check in HTTP_REQUIRED_PERSISTENCE:
                    raise F5OperationError(
                        f"Virtual server type '{vs_type}' can't use Cookie persistence (it requires "
                        f"HTTP-layer visibility that Fast L4/forwarding profiles don't provide). Choose "
                        f"'Source Address' persistence, or change the Virtual Server Type to 'standard' "
                        f"or 'performance-http'."
                    )

        type_map = {
            "standard": (prof.get("tcp", "/Common/tcp"), "tcp"),
            "forwarding-ip": (prof.get("ipother", "/Common/ipother"), "tcp"),
            "forwarding-l2": (prof.get("l2forward", "/Common/l2forward"), "tcp"),
            "reject": (prof.get("tcp", "/Common/tcp"), "tcp"),
            "dhcp": (prof.get("dhcpv4", "/Common/dhcpv4"), "udp"),
           "performance-http": (prof.get("http", "/Common/http"), "tcp"),
           "performance-l4": (prof.get("fastl4", "/Common/fastl4"), "tcp"),
           "internal": (prof.get("tcp", "/Common/tcp"), "tcp"),
        }
        primary_profile, default_protocol = type_map.get(vs_type, (prof.get("tcp", "/Common/tcp"), "tcp"))
    
        profiles = [primary_profile]
        if oneconnect_profile:
            oc = oneconnect_profile if isinstance(oneconnect_profile, str) else prof.get("oneconnect", "/Common/oneconnect")
            profiles.append(oc)
    
        resolved_persistence = None
        if persistence_profile and persistence_profile != "none":
            resolved_persistence = PERSISTENCE_PROFILE_MAP.get(persistence_profile, persistence_profile)
    
        # F5 rejects cookie persistence (01070309:3) unless an HTTP/FastHTTP
        # profile is already attached to the virtual server. Auto-add one
        # rather than making the user pick it manually.
        if resolved_persistence in HTTP_REQUIRED_PERSISTENCE and not any(p in HTTP_CLASS_PROFILES for p in profiles):
            profiles.append(prof.get("http", "/Common/http"))
    
        payload = {
            "name": vs_name,
            "partition": self.partition,
            "destination": destination,
            "ipProtocol": protocol or default_protocol,
            "profiles": profiles,
        }
        if vs_type not in no_pool_types:
            payload["pool"] = f"/{self.partition}/{pool_name}"
    
        if snat == "automap":
            payload["sourceAddressTranslation"] = {"type": "automap"}
        elif snat == "none":
            payload["sourceAddressTranslation"] = {"type": "none"}
        elif snat:
            payload["sourceAddressTranslation"] = {"type": "snat", "pool": snat}
    
        if resolved_persistence:
            payload["persist"] = [{"name": resolved_persistence}]
    
        resp = self._get(f"/ltm/virtual/~{self.partition}~{vs_name}")
        if resp.status_code == 200:
            patchable_keys = ("destination", "ipProtocol", "pool", "profiles", "sourceAddressTranslation", "persist")
            patchable = {k: v for k, v in payload.items() if k in patchable_keys}
            patch_resp = self._patch(f"/ltm/virtual/~{self.partition}~{vs_name}", patchable)
            if not self._ok(patch_resp):
                raise F5OperationError(f"Failed to reconcile virtual server '{vs_fqdn}': {patch_resp.text}")
            return vs_fqdn
    
        resp = self._post("/ltm/virtual", payload)
        if not self._ok(resp):
            raise F5OperationError(f"Failed to create virtual server '{vs_fqdn}': {resp.text}")
        return vs_fqdn


def _normalize_lb_mode(mode):
    if not mode:
        return "round-robin"
    if mode in LB_MODE_MAP.values():
        return mode
    if mode in LB_MODE_MAP:
        return LB_MODE_MAP[mode]
    return mode


def _require(mapping, key, what):
    if key not in mapping or mapping[key] in (None, ""):
        raise F5OperationError(
            f"Required field '{key}' ({what}) is missing from the request payload."
        )
    return mapping[key]


def handler(context, inputs):
    host = _require(inputs, "host", "F5 management host")
    username, password = _resolve_credentials(inputs, host)
    partition = inputs.get("partition") or "Common"
    verify_tls = bool(inputs.get("verify_tls", False))

    f5 = F5Manager(host, username, password, partition, verify_tls=verify_tls)

    vs = _require(inputs, "vs", "virtual server definition")
    pool = _require(inputs, "pool", "pool definition")

    vs_name = _require(vs, "name", "vs.name")
    destination_ip = (vs.get("destination_ip") or "").strip()
    if not destination_ip or destination_ip.lower() == "auto":
        subnet_entry = _vip_subnet_entry(inputs, host)
        cidr = subnet_entry.get("cidr") if subnet_entry else None
        if not cidr:
            raise F5OperationError(
                f"No VIP subnet configured for F5 host {host!r} in "
                f"F5_VIP_SUBNET_REGISTRY -- cannot auto-assign a destination IP. "
                f"Add an entry (Extensibility > Actions > Action Constants), or "
                f"supply vs.destination_ip explicitly."
            )
        reserved = subnet_entry.get("reserved") or []
        destination_ip = f5.next_available_ip(cidr, reserved=reserved)
    vs_type = vs.get("type", "standard")
    protocol = vs.get("protocol")
    snat = vs.get("snat")
    oneconnect_profile = vs.get("oneconnect_profile")
    persistence_profile = vs.get("persistence_profile")

    ports = vs.get("ports") or [_require(vs, "port", "vs.port (or vs.ports[])")]
    ports = [str(p) for p in ports]

    pool_name = _require(pool, "name", "pool.name")
    lb_mode = _normalize_lb_mode(pool.get("load_balancing_mode"))

    monitor_type = pool.get("monitor_type")
    if monitor_type:
        monitor_interval = pool.get("monitor_interval")
        monitor_timeout = pool.get("monitor_timeout")
        if monitor_interval or monitor_timeout:
            # Interval/timeout customized -- create a dedicated monitor object
            # for this pool so the custom timing only affects this pool
            # (doesn't touch F5's shared standard monitor's settings).
            monitor_name = pool.get("monitor_name") or f"{pool_name}_monitor"
            monitor = f5.create_monitor(
                monitor_name, monitor_type,
                interval=monitor_interval, timeout=monitor_timeout,
            )
        else:
            # No customization requested -- reuse F5's standard built-in
            # monitor for this type instead of creating a new object per pool.
            monitor = f"/Common/{monitor_type}"
    else:
        m = pool.get("monitor")
        monitor = None if (not m or m == "none") else m

    nodes = inputs.get("nodes", [])
    members_to_add = []
    for n in nodes:
        node_name = n.get("name")
        address = n.get("address")
        raw_port = n.get("port")
        if raw_port in (None, "", "null"):
            raise F5OperationError(
                f"Backend node '{node_name or address}' is missing a Port. "
                f"Every row in Backend Nodes must have a Port before a pool member can be created."
            )
        node_port = str(raw_port)
        create_if_missing = bool(n.get("create_if_missing", False))
        if not node_name:
            raise F5OperationError("Each node entry must include 'name' (fullPath preferred).")
        short_name = node_name.split("/", 2)[-1] if node_name.startswith("/") else node_name
        member_node_full_path = node_name if node_name.startswith("/") else f"/{partition}/{node_name}"
        if address and create_if_missing:
            f5.create_node(short_name, address)
        members_to_add.append({"node_full_path": member_node_full_path, "port": node_port})

    f5.create_pool(pool_name, monitor_name=monitor, load_balancing_mode=lb_mode)

    for m in members_to_add:
        f5.add_pool_member(pool_name, m["node_full_path"], m["port"])

    available_profiles = f5.list_profiles()
    created_vs = []
    for vs_port in ports:
        vs_name_for_port = vs_name if len(ports) == 1 else f"{vs_name}-{vs_port}"
        fqdn = f5.create_virtual_server(
            vs_name=vs_name_for_port, destination_ip=destination_ip, port=vs_port,
            pool_name=pool_name, vs_type=vs_type, protocol=protocol, snat=snat,
            oneconnect_profile=oneconnect_profile, persistence_profile=persistence_profile,
            available_profiles=available_profiles,
        )
        created_vs.append(fqdn)

    return {
        "virtualServers": created_vs,
        "poolName": f"/{partition}/{pool_name}",
        "destinationIp": destination_ip,
    }

