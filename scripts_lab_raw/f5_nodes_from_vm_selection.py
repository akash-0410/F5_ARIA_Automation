"""
ABX Action: f5_nodes_from_vm_selection
-----------------------------------------
Custom Form data source for the Backend Nodes Data Grid's Default value
(External source) binding. Turns whatever was picked in the "Backend VMs"
multi-select (f5_list_vcenter_vms) into editable grid rows -- Name and
Address from vCenter, Port left blank for the requester to set, and
"Create Node if Missing" defaulted to True since a VM straight out of
vCenter almost certainly isn't already registered as an F5 node.

The grid still allows manually adding extra rows for anything not in
vCenter -- this action only supplies rows from the multi-select; it never
removes the ability to add more by hand.

Inputs:
    selectedVms (array of "name|ip" strings, required) From the
                "Backend VMs" multi-select field.

Output:
    {"nodes": [{"name": "web-02", "port": None, "address": "10.10.1.9",
                "create_if_missing": True}, ...]}
"""

def handler(context, inputs):
    selected = inputs.get("selectedVms") or []
    if isinstance(selected, str):
        selected = [selected]

    nodes = []
    for entry in selected:
        if not entry or "|" not in entry:
            continue
        name, address = entry.split("|", 1)
        nodes.append({"name": name, "port": None, "address": address, "create_if_missing": True})
    return {"nodes": nodes}
