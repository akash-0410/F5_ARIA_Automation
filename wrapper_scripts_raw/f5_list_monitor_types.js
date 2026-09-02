// f5_list_monitors
// vRO wrapper for ABX action f5_list_monitors.
// Queries the live F5 device for existing health monitors.
// Inputs: host (required), partition (optional, default "Common").

var inputsObj = {
    "host": host
};
if (partition) {
    inputsObj.partition = partition;
}

var resultJson = System.getModule("com.f5.automation").f5_vra_run_action(
    "8a748097a00ff13901a03300d09706d9",
    JSON.stringify(inputsObj)
);
var result = JSON.parse(resultJson);
var options = (result && result.options) ? result.options : [];

var values = [];
for (var i = 0; i < options.length; i++) {
    values.push(options[i].value);
}
return values;