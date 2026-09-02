// f5_list_vcenter_vms
// vRO wrapper for ABX action f5_list_vcenter_vms.
// Inputs: location, environmentType -- forwarded to the ABX action so
// it's ready to filter by Location/Environment once the client's real
// vCenter has folder/tag organization (see FILTER_BY_LOCATION_ENV in
// the ABX action). Until then the action ignores these and returns the
// same VM list for every location.
//
// NOTE: a placeholder is always prepended so the Backend VMs multi-select
// never has exactly one option -- Aria Automation auto-selects a
// select-type field's value when it has only one possible option, which
// would silently pre-select a lone VM and populate Backend Nodes without
// the requester choosing anything. The placeholder itself contains no
// "|" so f5_nodes_from_vm_selection's filter (below) ignores it if it's
// ever left "selected".

var ACTION_ID = "8a748097a00ff13901a0331a482506e3";

var inputsObj = {
    "location": location,
    "environmentType": environmentType
};

var resultJson = System.getModule("com.f5.automation").f5_vra_run_action(
    ACTION_ID,
    JSON.stringify(inputsObj)
);
var result = JSON.parse(resultJson);
var options = (result && result.options) ? result.options : [];

var values = [];
values.push("-- Select VM(s) --");
for (var i = 0; i < options.length; i++) {
    values.push(options[i].value);
}
return values;