// f5_generate_deployment_name
// vRO wrapper action used as the "Deployment Name" field's Default value
// (External source) binding on the F5-Virtual-Server Custom Form.
// Inputs: project, location, environmentType -- mapped from the Basic
// tab's Project / Location / Environment Type fields.
//
// NOTE ON THE "project" INPUT: it is declared and mapped from the Custom
// Form but intentionally UNUSED below. Do not remove it -- removing a
// declared input that a Custom Form binding maps to silently breaks that
// binding without an obvious error, which is exactly how this action's
// original "GUID-prefixed deployment name" defect happened. Project was
// deliberately dropped from the generated name itself (see below); it
// stays in the signature only so the existing Custom Form binding keeps
// working unchanged.
//
// Builds a unique deployment name of the form:
//     <Location>-<EnvironmentType>-<seq>
// e.g. "site-a-production-0007"
//
// The sequence number is a persistent, per-prefix counter stored in the
// "F5-Automation/DeploymentNaming" Configuration Element (attribute:
// sequenceCounters, type Properties). It increments every time this
// action runs for a given location+environment combination -- including
// if the requester changes those fields before submitting -- so numbers
// can skip ahead but will never collide. Concurrent requests for the
// exact same combination at the exact same instant could in theory read
// the same counter value before either writes back; given this is a
// low-volume internal self-service form, that risk is treated as
// acceptable rather than solved with locking.
//
// SETUP REQUIRED (one-time, in the Orchestrator client):
//   Assets > Configurations > New folder "F5-Automation" > New configuration
//   element "DeploymentNaming" > add attribute "sequenceCounters",
//   type "Properties", leave value empty, save.
//   NOTE: this "F5-Automation" Configuration folder name is a literal
//   string this script depends on -- it is independent of whatever the
//   vRA *project* for this solution is named in your environment. Do not
//   rename this folder to match your project name.

function sanitize(value) {
    if (!value) {
        return "NA";
    }
    var s = String(value).trim();
    // If this looks like a raw GUID (e.g. the Project field's internal ID
    // rather than its display name), shorten it instead of embedding the
    // whole thing in the deployment name.
    var guidPattern = /^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/;
    if (guidPattern.test(s)) {
        s = s.substring(0, 8);
    }
    s = s.replace(/[^A-Za-z0-9]+/g, "-");
    s = s.replace(/^-+|-+$/g, "");
    return s.length ? s : "NA";
}

var prefix = sanitize(location) + "-" + sanitize(environmentType);

var category = Server.getConfigurationElementCategoryWithPath("F5-Automation");
if (!category) {
    throw "Configuration folder 'F5-Automation' not found -- create it in Assets > Configurations first (see action header comment).";
}

var element = null;
var elements = category.configurationElements;
for (var i = 0; i < elements.length; i++) {
    if (elements[i].name === "DeploymentNaming") {
        element = elements[i];
        break;
    }
}
if (!element) {
    throw "Configuration element 'DeploymentNaming' not found in folder 'F5-Automation' -- create it first (see action header comment).";
}

var attr = element.getAttributeWithKey("sequenceCounters");
var counters = attr.value;
if (!counters) {
    counters = new Properties();
}

var current = counters.get(prefix);
var next = current ? (parseInt(current, 10) + 1) : 1;
counters.put(prefix, String(next));
element.setAttributeWithKey("sequenceCounters", counters);
var seq = String(next);
while (seq.length < 4) {
    seq = "0" + seq;
}

return prefix + "-" + seq;
