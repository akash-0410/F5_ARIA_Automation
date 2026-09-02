// f5_list_environments
// vRO wrapper for ABX action f5_list_environments (actionId 8a74805da00e9db401a00ee534070004).
// No inputs. Returns the static Environment Type list (Production / UAT) as values.

var inputsObj = {};
var resultJson = System.getModule("com.f5.automation").f5_vra_run_action("8a74805da00e9db401a00ee534070004", JSON.stringify(inputsObj));
var result = JSON.parse(resultJson);
var options = (result && result.options) ? result.options : [];
var values = [];
for (var i = 0; i < options.length; i++) {
    values.push(options[i].value);
}
return values;