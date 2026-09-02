"""
ABX Action: f5_list_clusters
------------------------------
Custom Form data source for the "F5 Cluster" dropdown. Devices are now
maintained WITHOUT CODE via the org's Action Constants page
(Extensibility > Actions > Action Constants > F5_DEVICE_REGISTRY) -- edit
that JSON value directly in the vRA UI to add, rename, or remove F5
devices per Location and Environment; no changes to this script are ever
needed to onboard/retire a device.

F5_DEVICE_REGISTRY JSON shape:
{
  "<location value>": {
    "production": [{"label": "<display name>", "host": "<mgmt host/VIP>"}, ...],
    "uat":        [{"label": "<display name>", "host": "<mgmt host/VIP>"}, ...]
  },
  ...
}

Cascades off BOTH the "Location" dropdown (f5_list_locations) and the
"Environment Type" dropdown (f5_list_environments): pass the selected
location's value as "location" and the selected environment's value as
"environment". Each site keeps separate Production and UAT device pools,
so both inputs narrow the returned F5 Cluster options. If either is
omitted, this action falls back to returning all devices across the
un-filtered dimension (keeps it usable standalone / in TEST runs).

Inputs: location (optional -- value from f5_list_locations, e.g.
"chanakyapuri" / "secunderabad"), environment (optional -- value from
f5_list_environments, e.g. "production" / "uat")
Action Default Inputs required: F5_DEVICE_REGISTRY (Type = Action
constant, bound to the F5_DEVICE_REGISTRY action constant -- its JSON
text is what non-coders edit to update the device inventory).
Output: {"options": [{"label": "<device name>", "value": "<mgmt host/VIP>"}, ...]}
"""

import json


def handler(context, inputs):
    location = (inputs.get("location") or "").strip().lower()
    environment = (inputs.get("environment") or "").strip().lower()

    raw_registry = inputs.get("F5_DEVICE_REGISTRY")
    if isinstance(raw_registry, dict):
        registry = raw_registry
    else:
        registry = json.loads(raw_registry or "{}")
    locations = [location] if location else list(registry.keys())
    options = []
    for loc in locations:
        envs = registry.get(loc) or {}
        environments = [environment] if environment else list(envs.keys())
        for env in environments:
            for device in envs.get(env) or []:
                label = device.get("label")
                host = device.get("host")
                if label and host:
                    options.append({"label": label, "value": host})

    return {"options": options}
