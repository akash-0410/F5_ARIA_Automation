// f5_list_nodes
// vRO wrapper for ABX action f5_list_nodes (actionId 8a7480179fff2d51019fff8af2830006).
// Inputs: host (required), partition (optional, defaults to "Common"). Used for the
// Backend Server Configuration node search/select field.

var inputsObj = { host: host, partition: partition ? partition : "Common" };

var resultJson = System.getModule("com.f5.automation").f5_vra_run_action("8a7480179fff2d51019fff8af2830006", JSON.stringify(inputsObj));
var result = JSON.parse(resultJson);
var options = (result && result.options) ? result.options : [];
var values = [];
for (var i = 0; i < options.length; i++) {
    values.push(options[i].value);
}
return values;