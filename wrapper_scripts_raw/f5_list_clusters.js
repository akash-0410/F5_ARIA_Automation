// f5_list_clusters
// vRO wrapper for ABX action f5_list_clusters (actionId 8a74801798ff2d51019fff86f6f30002).
// Inputs: location (optional), environment (optional) - cascades the F5 Cluster dropdown
// off the Location and Environment Type fields upstream in the Custom Form.

var inputsObj = {};
if (location) { inputsObj.location = location; }
if (environment) { inputsObj.environment = environment; }

var resultJson = System.getModule("com.f5.automation").f5_vra_run_action("8a7480179fff2d51019fff86f6f30002", JSON.stringify(inputsObj));
var result = JSON.parse(resultJson);
var options = (result && result.options) ? result.options : [];
var values = [];
for (var i = 0; i < options.length; i++) {
    values.push(options[i].value);
    }
    return values;