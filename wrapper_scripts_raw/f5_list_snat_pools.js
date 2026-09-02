// f5_list_snat_pools
// vRO wrapper for ABX action f5_list_snat_pools (actionId 8a74805da00e9db401a00ed7acf90001).
// Inputs: host (required) - bound from the F5 Cluster field's value upstream.
//         username, password (optional) - if supplied, passed straight through to the
//         ABX action's directly-supplied-credential fallback, bypassing the
//         F5_CREDENTIAL_MAP Secret lookup entirely.

var inputsObj = { host: host };
//if (username) { inputsObj.username = username; }
//if (password) { inputsObj.password = password; }

var resultJson = System.getModule("com.f5.automation").f5_vra_run_action("8a74805da00e9db401a00ed7acf90001", JSON.stringify(inputsObj));
var result = JSON.parse(resultJson);
var options = (result && result.options) ? result.options : [];
var values = [];
for (var i = 0; i < options.length; i++) {
    values.push(options[i].value);
}
return values;
