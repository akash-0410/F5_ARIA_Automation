// f5_list_oneconnect_profiles
// vRO wrapper for ABX action f5_list_oneconnect_profiles (actionId 8a74805da00e9db401a00ee1a9730002).
// Input: host (required) - bound from the F5 Cluster field's value upstream.

var inputsObj = { host: host };

var resultJson = System.getModule("com.f5.automation").f5_vra_run_action("8a74805da00e9db401a00ee1a9730002", JSON.stringify(inputsObj));
var result = JSON.parse(resultJson);
var options = (result && result.options) ? result.options : [];
var values = [];
for (var i = 0; i < options.length; i++) {
    values.push(options[i].value);
}
return values;