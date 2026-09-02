// f5_list_lb_modes
// vRO wrapper for ABX action f5_list_lb_modes (actionId 8a7480179fff2d51019fff87ef050003).
// Queries the F5 device for LB methods in use across existing pools.
// Inputs: host (required).

var inputsObj = {
    "host": host
};

var resultJson = System.getModule("com.f5.automation").f5_vra_run_action(
    "8a7480179fff2d51019fff87ef050003",
    JSON.stringify(inputsObj)
);
var result = JSON.parse(resultJson);
var options = (result && result.options) ? result.options : [];

var values = [];
for (var i = 0; i < options.length; i++) {
    values.push(options[i].value);
}
return values;