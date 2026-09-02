// f5_list_free_ips
// vRO wrapper for ABX action f5_list_free_ips.
// Returns free/suggested IP addresses for the "Virtual IP Address" Custom Form field.
// Inputs: host (required, bound to the F5 Cluster dropdown).

var inputsObj = {
  "host": host
};

var resultJson = System.getModule("com.f5.automation").f5_vra_run_action(
  "8a748097a00ff13901a01d9a33b2014f",
  JSON.stringify(inputsObj)
);
var result = JSON.parse(resultJson);
var options = (result && result.options) ? result.options : [];

var values = [];
for (var i = 0; i < options.length; i++) {
  values.push(options[i].value);
}
return values;