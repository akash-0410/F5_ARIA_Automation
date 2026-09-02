"""
ABX Action: f5_list_vcenter_vms
---------------------------------
Custom Form data source for the "Backend VMs" multi-select field. Lists
existing VMs from vCenter so a requester picks real servers instead of
typing node details by hand. Each option's value carries both the VM's
name and its guest IP ("name|ip") so the dependent Backend Nodes grid
(f5_nodes_from_vm_selection) can build rows without a second vCenter call.

Inputs are location + environmentType because in the real client vCenter,
VMs will be organized per Location and Environment (folders or tags) and
this action will filter to just that scope. Today's lab vCenter has no
such organization yet, so filtering is temporarily disabled -- every
call returns the same set of VMs (minus known infra appliances) no
matter what location/environmentType come in. Flip
FILTER_BY_LOCATION_ENV to True once the client's vCenter is organized
that way (folder-per-location/environment is assumed below; swap in a
tag-based lookup instead if that's how they actually organize it).

Inputs:
    location              (string, required)  From the "Location" field.
    environmentType        (string, required)  From "Environment Type".
    vcenter_username       (string, Default Input)
    VCENTER_PASSWORD       (string, Default Input, secret)
    vcenter_host           (string, Default Input)  e.g. "vcenter.lab.internal"
    verify_tls              (bool, optional)  Defaults to False.

Output:
    {"options": [{"label": "DNS_SDS (172.16.1.50)", "value": "DNS_SDS|172.16.1.50"}, ...]}
"""
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

VCENTER_SECRET_KEY = "VCENTER_PASSWORD"

# Set True once the client vCenter organizes VMs per Location/Environment
# (folders or tags) -- and confirm/adjust the folder-name convention in
# _find_folder_id's caller below to match how they actually name folders.
FILTER_BY_LOCATION_ENV = False

# VM names (case-insensitive substring match) to always leave out of the
# picker -- platform/infrastructure appliances, not backend app servers.
EXCLUDED_NAME_SUBSTRINGS = ["bigip", "vidm", "lcm appliance", "vmware vcenter", "vra2"]

def _raise_for_status(resp):
    if resp.status_code >= 400:
        raise RuntimeError("vCenter API error {} for {}: {}".format(
            resp.status_code, resp.url, resp.text[:500]
        ))

def _scalar(value):
    if isinstance(value, list):
        return value[0] if value else ""
    if isinstance(value, dict):
        return value.get("value", "")
    return value or ""


def _resolve_credentials(inputs):
    username = inputs.get("vcenter_username")
    password = inputs.get(VCENTER_SECRET_KEY)
    if not username or not password:
        raise RuntimeError("vCenter credentials missing: username={}, password={}".format(
            "set" if username else "MISSING", "set" if password else "MISSING"
        ))
    return username, password


def _login(session, vcenter_host, username, password):
    resp = session.post("https://{}/api/session".format(vcenter_host), auth=(username, password), timeout=15)
    _raise_for_status(resp)
    session.headers.update({"vmware-api-session-id": resp.json()})


def _guest_ip(session, vcenter_host, vm_id):
    resp = session.get(
        "https://{}/api/vcenter/vm/{}/guest/networking/interfaces".format(vcenter_host, vm_id),
        timeout=15,
    )
    if resp.status_code != 200:
        return None
    for iface in resp.json():
        for ip in iface.get("ip", {}).get("ip_addresses", []):
            addr = ip.get("ip_address")
            if addr and ":" not in addr:
                return addr
    return None


def _is_excluded(name):
    lowered = name.lower()
    return any(substr in lowered for substr in EXCLUDED_NAME_SUBSTRINGS)


def _find_folder_id(session, vcenter_host, folder_name):
    resp = session.get(
        "https://{}/api/vcenter/folder".format(vcenter_host),
        params={"filter.names": folder_name, "filter.type": "VIRTUAL_MACHINE"},
        timeout=15,
    )
    resp.raise_for_status()
    folders = resp.json()
    return folders[0]["folder"] if folders else None


def handler(context, inputs):
    location = _scalar(inputs.get("location"))
    environment = _scalar(inputs.get("environmentType"))
    vcenter_host = inputs.get("vcenter_host")
    if not vcenter_host:
        raise RuntimeError("Missing required input 'vcenter_host'")
    if not location or not environment:
        raise RuntimeError("Missing required input 'location' or 'environmentType'")

    username, password = _resolve_credentials(inputs)
    verify_tls = bool(inputs.get("verify_tls", False))

    session = requests.Session()
    session.verify = verify_tls
    _login(session, vcenter_host, username, password)

    params = {}

    if FILTER_BY_LOCATION_ENV:
        folder_name = "{}/{}".format(location, environment)
        folder_id = _find_folder_id(session, vcenter_host, folder_name)
        if not folder_id:
            return {"options": []}
        params["filter.folders"] = folder_id

    resp = session.get(
        "https://{}/api/vcenter/vm".format(vcenter_host),
        params=params,
        timeout=15,
    )
    _raise_for_status(resp)

    options = []
    for vm in resp.json():
        if vm.get("power_state") != "POWERED_ON":
            continue
        name = vm.get("name", "")
        if not name or _is_excluded(name):
            continue
        ip = _guest_ip(session, vcenter_host, vm["vm"])
        if not ip:
            continue
        options.append({"label": "{} ({})".format(name, ip), "value": "{}|{}".format(name, ip)})

    options.sort(key=lambda o: o["label"])
    return {"options": options}
