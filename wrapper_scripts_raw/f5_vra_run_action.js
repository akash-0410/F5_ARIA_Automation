// f5_vra_run_action
// Generic vRO wrapper: synchronously invokes a vRA ABX Extensibility Action via
// its action-runs REST API and returns the run's outputs as a JSON string.
// Called by the 9 f5_list_* wrapper actions (module com.f5.automation) so the
// Custom Form designer's "External source" dropdown binding -- which can only
// search/bind vRO actions, never ABX actions directly -- has something to bind to.
//
// Inputs:
//   actionId   (string) - the vRA ABX Extensibility Action ID (Assembler > Extensibility > Actions > open action > id in URL)
//   inputsJson (string) - JSON-encoded object of inputs to pass to the ABX action, e.g. '{"host":"172.16.1.205"}' or "{}" for none
// Output: JSON string of the ABX action's "outputs" object (whatever handler() returned)
//
// Credential (v2 design): this on-prem/embedded vRA build has no "Service Accounts"
// concept, so a bare vIDM OAuth2 Client Credentials token authenticates fine but is
// never authorized (401) against project-scoped APIs like ABX action-runs -- only
// real user identities are recognized here. This action instead exchanges the
// 'vraRefreshToken' attribute (a long-lived vRA refresh token for the 'configadmin'
// user, an Organization Owner) for a fresh short-lived Bearer access token on every
// call via POST /iaas/api/login. No access token is ever stored -- only the refresh
// token, which is expected to be long-lived -- so nothing needs frequent manual
// refresh. Populate 'vraRefreshToken' manually in the Orchestrator UI (Configuration
// Element "F5-Automation-Credentials", category "web-root") by obtaining it once via
// POST /csp/gateway/am/api/login as configadmin. This action does not, and must not,
// hardcode or log either the refresh token or any minted access token.

var VRA_HOST = "https://vra.lab.internal";
var PROJECT_ID = "d347d2fd-4e27-4a0d-b144-f5262d7a70a1";
var CONFIG_CATEGORY_PATH = "web-root";
var CONFIG_ELEMENT_NAME = "F5-Automation-Credentials";
var MAX_POLL_ATTEMPTS = 30;
var POLL_INTERVAL_MS = 1000;

// 1. Look up the vRA refresh token from the Configuration Element.
var category = Server.getConfigurationElementCategoryWithPath(CONFIG_CATEGORY_PATH);
if (!category) {
    throw "Configuration category '" + CONFIG_CATEGORY_PATH + "' not found.";
}
var configElement = null;
var elements = category.configurationElements;
for (var i = 0; i < elements.length; i++) {
    if (elements[i].name === CONFIG_ELEMENT_NAME) {
        configElement = elements[i];
        break;
    }
}
if (!configElement) {
    throw "Configuration Element '" + CONFIG_ELEMENT_NAME + "' not found in category '" + CONFIG_CATEGORY_PATH + "'.";
}
var refreshTokenAttr = configElement.getAttributeWithKey("vraRefreshToken");
var refreshToken = refreshTokenAttr ? refreshTokenAttr.value : null;
if (!refreshToken) {
    throw "Configuration Element '" + CONFIG_ELEMENT_NAME + "' is missing 'vraRefreshToken'. " +
          "An administrator must populate it (obtained via POST /csp/gateway/am/api/login as configadmin) before this action can run.";
}

// 2. Build the transient REST host for vRA.
var vraHostDef = RESTHostManager.createHost("f5-vra-transient");
vraHostDef.url = VRA_HOST;
var restHost = RESTHostManager.createTransientHostFrom(vraHostDef);
restHost.operationTimeout = 60;
restHost.connectionTimeout = 30;
restHost.hostVerification = false;

// 3. Exchange the refresh token for a fresh short-lived Bearer access token.
var loginBody = JSON.stringify({ refreshToken: refreshToken });
var loginRequest = restHost.createRequest("POST", "/iaas/api/login", loginBody);
loginRequest.contentType = "application/json";

var loginResponse = loginRequest.execute();
if (loginResponse.statusCode >= 300) {
    throw "POST /iaas/api/login failed (" + loginResponse.statusCode + "): " + loginResponse.contentAsString;
}
var loginObj = JSON.parse(loginResponse.contentAsString);
var token = loginObj.token;
if (!token) {
    throw "POST /iaas/api/login response did not include a token.";
}

// 4. Kick off the ABX action run.
var parsedInputs = {};
try {
    parsedInputs = JSON.parse(inputsJson || "{}");
} catch (e) {
    throw "inputsJson is not valid JSON: " + inputsJson;
}
var runBody = JSON.stringify({ projectId: PROJECT_ID, inputs: parsedInputs });

var createRequest = restHost.createRequest("POST", "/abx/api/resources/actions/" + actionId + "/action-runs", runBody);
createRequest.setHeader("Authorization", "Bearer " + token);
createRequest.contentType = "application/json";

var createResponse = createRequest.execute();
if (createResponse.statusCode >= 300) {
    throw "POST /abx/api/resources/actions/" + actionId + "/action-runs failed (" +
          createResponse.statusCode + "): " + createResponse.contentAsString;
}
var runObj = JSON.parse(createResponse.contentAsString);
var runId = runObj.id;
var runState = runObj.runState;
var outputs = runObj.outputs;

// 5. Poll until the run completes.
var attempts = 0;
while (runState !== "COMPLETED" && runState !== "FAILED" && runState !== "CANCELLED" && attempts < MAX_POLL_ATTEMPTS) {
    System.sleep(POLL_INTERVAL_MS);
    var pollRequest = restHost.createRequest("GET", "/abx/api/resources/action-runs/" + runId, null);
    pollRequest.setHeader("Authorization", "Bearer " + token);
    var pollResponse = pollRequest.execute();
    if (pollResponse.statusCode >= 300) {
        throw "GET /abx/api/resources/action-runs/" + runId + " failed (" +
              pollResponse.statusCode + "): " + pollResponse.contentAsString;
    }
    var pollObj = JSON.parse(pollResponse.contentAsString);
    runState = pollObj.runState;
    outputs = pollObj.outputs;
    attempts++;
}

if (runState !== "COMPLETED") {
    throw "ABX action run " + runId + " for actionId=" + actionId + " did not complete (final state=" + runState + ").";
}

return JSON.stringify(outputs);
