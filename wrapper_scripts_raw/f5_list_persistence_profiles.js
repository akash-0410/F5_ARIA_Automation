// f5_list_persistence_profiles
// vRO wrapper for ABX action f5_list_persistence_profiles.
// Queries the F5 device for existing persistence profiles.
// Inputs: host (required), partition (optional).

var inputsObj = {
    "host": host
};
if (partition) {
    inputsObj.partition = partition;
}

var resultJson = System.getModule("com.f5.automation").f5_vra_run_action(
    "8a7480179fff2d51019fff88ca6f0004",
    JSON.stringify(inputsObj)
);
var result = JSON.parse(resultJson);
var options = (result && result.options) ? result.options : [];

var values = [];
for (var i = 0; i < options.length; i++) {
    values.push(options[i].value);
}
return values;