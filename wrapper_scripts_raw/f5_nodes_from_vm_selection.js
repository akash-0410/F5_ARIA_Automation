// f5_nodes_from_vm_selection
// vRO wrapper for ABX action f5_nodes_from_vm_selection (project F5-Automation).
// Input: selectedVms (array of "name|ip" strings from the "Backend VMs"
// multi-select field). Used as the Backend Nodes Data Grid field's Default
// value (External source) binding -- returns one editable grid row per
// selected VM (Properties object keyed to match the grid's column IDs:
// name, port, address, create_if_missing).
//
// Only genuine "name|ip" entries are forwarded -- this drops the
// "-- Select VM(s) --" placeholder (and any blank/undefined values) so
// the grid stays empty until the requester actually picks a real VM.

var ACTION_ID = "8a748097a00ff13901a0331afa2906e4";

var filteredVms = [];
if (selectedVms) {
    for (var i = 0; i < selectedVms.length; i++) {
        if (selectedVms[i] && selectedVms[i].indexOf("|") !== -1) {
            filteredVms.push(selectedVms[i]);
        }
    }
}

if (filteredVms.length === 0) {
    return [];
}

var inputsObj = { selectedVms: filteredVms };

var resultJson = System.getModule("com.f5.automation").f5_vra_run_action(ACTION_ID, JSON.stringify(inputsObj));
var result = JSON.parse(resultJson);
var nodes = (result && result.nodes) ? result.nodes : [];

var rows = [];
for (var i = 0; i < nodes.length; i++) {
	var row = new Properties();
	row.put("name", nodes[i].name);
	row.put("port", nodes[i].port);
	row.put("address", nodes[i].address);
	row.put("create_if_missing", nodes[i].create_if_missing);
	rows.push(row);
}
return rows;