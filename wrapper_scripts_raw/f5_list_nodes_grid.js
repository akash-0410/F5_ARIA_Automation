// f5_list_nodes_grid
// vRO wrapper for ABX action f5_list_nodes_grid (project F5-Automation).
// Inputs: host (required), partition (optional, defaults to "Common"). Used as the
// Backend Nodes Data Grid field's Default value (External source) binding -- returns
// existing F5 nodes as pre-filled, editable grid rows (one Properties object per row,
// keyed to match the grid's column IDs: name, port, address, create_if_missing).
//
// IMPORTANT: replace ACTION_ID below with the real id of the new f5_list_nodes_grid
// ABX action once it's created (Extensibility Actions > f5_list_nodes_grid > General
// tab, or copy it out of the URL the same way the other wrappers do).

var ACTION_ID = "8a748097a00ff13901a01eb4de840327";

var inputsObj = { host: host, partition: partition ? partition : "Common" };

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