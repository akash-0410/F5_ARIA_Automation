// f5_list_locations
// vRO wrapper for ABX action f5_list_locations (actionId 8a74805da00e9db401a00ecdfb140000).
// No inputs. Returns the static Location list (Chanakyapuri / Secunderabad) as values.

var inputsObj = {};
var resultJson = System.getModule("com.f5.automation").f5_vra_run_action("8a74805da00e9db401a00ecdfb140000", JSON.stringify(inputsObj));
var result = JSON.parse(resultJson);
var options = (result && result.options) ? result.options : [];
var values = [];
for (var i = 0; i < options.length; i++) {
    values.push(options[i].value);
}
return values;