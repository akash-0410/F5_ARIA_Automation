// Content for SOP.docx, expressed in the render.js mini-DSL.
// Facts here are drawn directly from the verified, live-fetched source of
// scripts/f5_generate_deployment_name.js and scripts/f5_create_virtual_server.py.

const TITLE_BLOCKS = [
  { spacer: 2000 },
  { p: [{ text: 'F5 AUTOMATION SOLUTION', bold: true }], opts: { center: true } },
  { p: [{ text: 'Standard Operating Procedure', bold: true }], opts: { center: true } },
  { spacer: 200 },
  { p: [{ text: 'Deployment, Configuration, and Operations Reference' }], opts: { center: true } },
  { spacer: 800 },
  { p: [{ text: 'Version 2.0' }], opts: { center: true } },
  { p: [{ text: 'Prepared: 2026-08-31' }], opts: { center: true } },
  { p: [{ text: 'Owner: Automation Engineering' }], opts: { center: true } },
  { spacer: 1600 },
  { p: [{ text: 'Companion document: DEPLOYMENT_GUIDE.md (Tier-1 / L1 click-by-click instructions)', italics: true }], opts: { center: true } },
  { pageBreak: true },
];

const DOC_CONTROL = [
  { h1: 'Document Control' },
  { table: {
      headers: ['Version', 'Date', 'Author', 'Summary of changes'],
      widths: [12, 14, 24, 50],
      rows: [
        ['1.0', '2026-08-31', 'Automation Engineering', 'Initial SOP: deployment-naming GUID fix and ABX indentation fix, process-level detail only.'],
        ['2.0', '2026-08-31', 'Automation Engineering', 'Full technical reference edition: feature-by-feature functionality, complete configuration reference, embedded code excerpts, and a full glossary. Companion Deployment Guide rewritten for a Tier-1/L1 audience.'],
      ],
    },
  },
  { spacer: 200 },
  { h2: 'Contents' },
  { ul: [
      '1. Purpose and Scope',
      '2. Solution Overview',
      '3. Glossary of Terms',
      '4. Roles and Responsibilities',
      '5. Feature Reference — Deployment Naming (f5_generate_deployment_name)',
      '6. Feature Reference — F5 Virtual Server Provisioning (f5_create_virtual_server)',
      '7. Configuration Reference',
      '8. The Bug Fixes — What Changed and Why',
      '9. Change Management',
      '10. Deployment Procedure (Summary)',
      '11. Verification and Testing (Acceptance Criteria)',
      '12. Known Risks, Gaps, and Decisions Needed Before Go-Live',
      '13. Rollback Plan',
      '14. Post-Deployment Operations',
      '15. Approval and Sign-off',
      '16. Document History',
    ],
  },
  { pageBreak: true },
];

const SEC1_PURPOSE = [
  { h1: '1. Purpose and Scope' },
  { h2: '1.1 Purpose' },
  { p: 'This document is the complete technical and process reference for the F5 Automation solution built on VMware Aria Automation (vRA) and Aria Automation Orchestrator (vRO). It exists so that anyone — the original engineer, a new team member, a client\'s own staff, or an auditor — can understand what the solution does, how it is configured, why it behaves the way it does, and how to operate and maintain it safely, without needing to reverse-engineer the code from scratch.' },
  { p: 'This is a technical reference document. For step-by-step deployment instructions written for a Tier-1 (L1) engineer with no prior vRA/vRO experience, use the companion DEPLOYMENT_GUIDE.md instead. This SOP explains the "what" and "why"; the Deployment Guide explains the "click here, then here."' },
  { h2: '1.2 Scope' },
  { p: 'In scope: the two automation components that make up this solution, their configuration, their behavior, known limitations, deployment process, verification, and rollback.' },
  { ul: [
      'f5_generate_deployment_name — a vRO Action that generates the human-readable name for each F5 virtual server request.',
      'f5_create_virtual_server — a vRA ABX (Extensibility) Action that performs the actual F5 BIG-IP configuration (nodes, pool, virtual server) for a request.',
    ],
  },
  { p: 'Out of scope: the F5 BIG-IP device\'s own configuration and licensing, network/firewall connectivity between vRA/vRO and the F5 management plane, and the vRA Custom Form/Custom Resource definitions themselves (this SOP describes how this solution uses them, but does not govern how to build a Custom Form or Custom Resource from scratch).' },
  { pageBreak: true },
];

const SEC2_OVERVIEW = [
  { h1: '2. Solution Overview' },
  { p: 'The solution lets an end user request an F5 load-balancer configuration (nodes, a pool, and one or more virtual servers) through a self-service form, without needing direct F5 access or knowledge of the iControl REST API. Two automation components make this work, connected through vRA\'s Custom Form and Custom Resource framework:' },
  { h3: '2.1 Request-time flow (Deployment Naming)' },
  { ol: [
      'A user opens the F5 Virtual Server catalog item in vRA\'s Service Broker and starts filling out the Custom Form.',
      'As soon as Location and Environment Type are selected, the Custom Form calls the vRO Action f5_generate_deployment_name (an "External source" field binding) to compute the Deployment Name shown on the form.',
      'The action reads/increments a persistent sequence counter stored in a vRO Configuration Element, and returns a name like site-a-production-0002.',
      'The user reviews the form (including the auto-filled name) and submits the request.',
    ],
  },
  { h3: '2.2 Provisioning flow (Virtual Server Creation)' },
  { ol: [
      'On submission, vRA creates a Deployment containing an F5.VirtualServer Custom Resource with the values the user supplied.',
      'vRA invokes the ABX Action f5_create_virtual_server (the resource\'s create/update handler) inside its own isolated Python sandbox.',
      'The action resolves F5 credentials from its own Default/Secret Inputs (never from the request itself), resolves or auto-assigns a destination IP, then calls the F5 BIG-IP iControl REST API to create/reconcile the backend node(s), the pool, and the virtual server(s).',
      'The action returns the resulting object paths and destination IP, which vRA stores against the deployment.',
    ],
  },
  { h3: '2.3 Why two separate components' },
  { p: 'vRO Actions and vRA ABX Actions are architecturally different systems (different runtime, different editor, different execution model), even though both are informally called "actions." The naming action is a lightweight, synchronous JavaScript call well suited to filling in a form field in real time. The provisioning action is a heavier Python job that makes multiple external HTTP calls to F5 and is better suited to vRA\'s ABX/FaaS extensibility model, which runs at deployment time rather than as the user types.' },
  { note: 'Because these are two separate systems, a fix or change to one never automatically applies to the other — each must be deployed and verified independently, as covered in the Deployment Guide.' },
  { pageBreak: true },
];

const GLOSSARY_ROWS = [
  ['ABX Action', 'A Python or Node.js function hosted by vRA\'s own built-in serverless layer, edited under Extensibility > Actions inside vRA itself. Not the same system as a vRO Action, despite the shared word "action."'],
  ['Action Constant', 'A named value (often structured data such as JSON) attached to an ABX action. Visible to anyone who can view the action\'s configuration — not encrypted, so never used for secrets. Used here for F5_VIP_SUBNET_REGISTRY.'],
  ['ast.parse', 'A Python standard-library function that checks whether source code is syntactically valid without executing it. Used to confirm the ABX action\'s script has no syntax errors after edits.'],
  ['Attribute (vRO Configuration Element)', 'A single named value stored inside a vRO Configuration Element — analogous to a field in a small record. This solution uses one attribute, sequenceCounters, of type Properties.'],
  ['BIG-IP', 'F5\'s load-balancer / application-delivery-controller product. The physical or virtual device this automation configures.'],
  ['Catalog item (vRA)', 'A published, requestable item in vRA\'s Service Broker storefront — e.g. "F5 Virtual Server Request." Requesting one launches its Custom Form.'],
  ['CIDR', 'Classless Inter-Domain Routing notation for describing a network address range, e.g. 10.20.30.0/24.'],
  ['Configuration Element', 'A vRO object used to store small amounts of persistent data across action runs, organized into named folders called categories. This solution stores its deployment-name sequence counters in one.'],
  ['Custom Form', 'The request screen vRA renders for a catalog item, built from named fields. A field\'s value can come from a static default, another field, user input, or an external action ("External source").'],
  ['Custom Resource', 'A vRA construct describing an external resource type not natively understood by vRA (here, F5.VirtualServer), whose create/update/delete lifecycle is implemented by ABX actions instead of built-in vRA logic.'],
  ['Default Input', 'A static value attached to a vRO or ABX action. Always stored and displayed in plain text — never appropriate for passwords or other secrets.'],
  ['Dependency (ABX)', 'A Python package (e.g. requests) that the ABX action\'s runtime installs automatically before running the script, configured in the action\'s Dependency field.'],
  ['Deployment', 'One completed or in-progress request in vRA — has its own name, ID, resources, and lifecycle.'],
  ['External source (Custom Form)', 'A Custom Form field configuration where the field\'s value is computed by calling a vRO or ABX action, rather than being typed by the user or set to a static default.'],
  ['F5OperationError', 'A custom Python exception class defined inside f5_create_virtual_server.py. Every expected/handled failure in the script raises this type, so calling code (and log readers) can distinguish "the script detected and explained a problem" from an unexpected crash.'],
  ['FaaS (Function-as-a-Service)', 'The serverless execution model ABX actions run under: each run gets an isolated, short-lived sandbox with its declared dependencies installed and no access to any other files on the automation platform.'],
  ['Fast L4', 'An F5 virtual server type/profile family (performance-l4 in this solution) optimized for raw throughput at the network layer, with no HTTP-layer visibility — which is why it cannot combine with HTTP-dependent features like OneConnect or Cookie persistence (see Section 6.9).'],
  ['Field binding', 'The configured relationship between a Custom Form field and where its value comes from (static value, another field, or an action\'s input/output).'],
  ['GUID', 'Globally Unique Identifier — a long, machine-generated ID string (e.g. a vRA project\'s internal ID). Meant for computers to reference, not for humans to read; the original naming bug this solution fixes was a GUID leaking into a human-facing name.'],
  ['Handler', 'The specific function name vRA calls to run an ABX action. In this solution it is literally named handler and configured in the action\'s "Main function" setting.'],
  ['Hard refresh', 'A full, cache-bypassing browser reload (Ctrl/Cmd+Shift+R or Ctrl+F5), as opposed to a normal refresh. Needed when working in vRA/vRO because their admin screens can otherwise show stale, already-cached data after a save.'],
  ['iControl REST API', 'F5\'s HTTP/JSON management API. This ABX action talks to the F5 device exclusively through this API — end users and vRA never access it directly.'],
  ['IndentationError', 'A Python error raised when a script\'s whitespace does not correctly indicate which block of code a line belongs to. This is the exact defect class originally reported and fixed in the create_monitor() function (see Section 8).'],
  ['JSON (JavaScript Object Notation)', 'A structured text format for representing data (objects, lists, strings, numbers) that both humans and machines can read. Used here for the F5_VIP_SUBNET_REGISTRY Action Constant\'s value and for the F5 API\'s request/response bodies.'],
  ['JSONDecodeError', 'The Python error raised when text that is supposed to be JSON cannot actually be parsed as JSON (e.g. a missing comma or quote). This deployment\'s hardening pass replaced an unhandled JSONDecodeError with a clear F5OperationError message when F5_VIP_SUBNET_REGISTRY is malformed (see Section 8.3).'],
  ['KeyError', 'A Python error raised when code looks up a dictionary key that doesn\'t exist. Before this deployment\'s hardening pass, a missing required request field surfaced as an opaque KeyError instead of a clear message (see Section 8.3).'],
  ['Maintenance window', 'A pre-agreed time period during which a change is permitted to be made, per the client\'s change-management process (see Section 9).'],
  ['Monitor (F5 health monitor)', 'A periodic health check F5 runs against each pool member to decide whether it is currently eligible to receive traffic.'],
  ['Node (F5)', 'A backend server\'s IP address registered on the F5 device. A single node can be reused as a member of more than one pool.'],
  ['OneConnect profile', 'An F5 profile that lets the device reuse existing server-side TCP connections across multiple client requests, improving performance for HTTP-class traffic. Incompatible with Fast L4/forwarding virtual server types.'],
  ['Partition (F5)', 'A namespace on the F5 device grouping related objects (nodes, pools, virtual servers) together. Most environments use a single partition named Common.'],
  ['Persistence profile', 'An F5 setting that keeps a given client\'s traffic going to the same pool member for the life of a session (for example, via a cookie or the client\'s source IP).'],
  ['Pool (F5)', 'A named group of backend nodes (each with a port) that a virtual server distributes traffic across according to a load-balancing mode and health monitor.'],
  ['Pool member', 'One specific node+port combination that belongs to a pool.'],
  ['Project (vRA)', 'An administrative container in vRA grouping users, resources, and permissions. Every request and deployment belongs to exactly one project. Not the same thing as the vRO "F5-Automation" Configuration folder — see Section 7.3.'],
  ['py_compile', 'A Python standard-library tool that compiles a script to confirm it contains no syntax errors, without running its logic. Used as the primary regression check for the fix in Section 8.2.'],
  ['RuntimeError', 'A general-purpose Python exception. Before this deployment\'s hardening pass, the credential-check failure raised a bare RuntimeError instead of this script\'s own F5OperationError type (see Section 8.3).'],
  ['Secret (input type)', 'An input value type where, once saved, the plaintext can never be read back through the UI or API — the only appropriate storage type for a password such as the F5 device credential.'],
  ['self IP (F5)', 'An IP address assigned directly to the F5 device\'s own network interface (as opposed to a virtual server\'s client-facing VIP). next_available_ip() automatically excludes a host\'s self IPs when auto-assigning a VIP — see Section 6.5.'],
  ['Sequence counter', 'The auto-incrementing number this solution appends to each generated deployment name (e.g. the 0002 in site-a-production-0002) so that no two deployments for the same location/environment ever receive the same name.'],
  ['Service Broker', 'The area of vRA where end users browse and request published catalog items — effectively vRA\'s storefront.'],
  ['SNAT (Source Network Address Translation)', 'F5 configuration that controls what source IP address backend servers see when traffic arrives via the virtual server.'],
  ['SyntaxError', 'A general Python error meaning the script\'s text cannot be parsed as valid Python at all. IndentationError (see above) is one specific kind of SyntaxError.'],
  ['TLS (Transport Layer Security)', 'The encryption protocol behind HTTPS. verify_tls controls whether this action checks the F5 device\'s TLS certificate when calling its API — see Section 12, item 3.'],
  ['tokenize (Python)', 'A Python standard-library module that breaks source code into lexical tokens. Used as an additional, independent syntax/indentation consistency check alongside ast.parse.'],
  ['urllib3', 'The HTTP library the requests package is built on. This script calls urllib3.disable_warnings() to silence the certificate warnings that result from verify_tls defaulting to off — see Section 12, item 3.'],
  ['VIP (Virtual IP)', 'The client-facing IP address assigned to a virtual server.'],
  ['Virtual Server (F5) / VS', 'The load balancer\'s actual traffic-facing endpoint — an IP + port combination that receives client connections and forwards them to a pool.'],
  ['vRA (Aria Automation)', 'VMware/Broadcom\'s self-service cloud automation platform — the front end end users interact with to request resources. Sometimes shown in its UI as "Assembler."'],
  ['vRO (Aria Automation Orchestrator)', 'The workflow/scripting engine bundled with vRA, shown in its own UI as "Embedded-VRO." Hosts the JavaScript Actions used for lighter-weight logic such as the deployment-naming action.'],
];

const SEC3_GLOSSARY = [
  { h1: '3. Glossary of Terms' },
  { p: 'Every technical term used anywhere in this SOP or the companion Deployment Guide is defined below, in alphabetical order. If you are new to vRA/vRO/F5, read this section fully before continuing — the rest of the document assumes these definitions.' },
  { table: { headers: ['Term', 'Definition'], widths: [28, 72], rows: GLOSSARY_ROWS } },
  { pageBreak: true },
];

const SEC4_ROLES = [
  { h1: '4. Roles and Responsibilities' },
  { table: {
      headers: ['Role', 'Responsibility'],
      widths: [26, 74],
      rows: [
        ['Deploying engineer', 'Executes the Deployment Guide step by step; owns the pre-deployment backup and the verification evidence.'],
        ['Change approver', 'Approves the maintenance window and reviews the rollback plan before work begins, per the client\'s change-management policy.'],
        ['F5 / network owner', 'Confirms F5 cluster host details, VIP subnets, and credentials to be used are correct for the target environment before deployment starts; reviews the "decisions needed before go-live" items in Section 12.'],
        ['Client point of contact', 'Notified before and after the change; confirms the environment and project names used throughout this SOP.'],
        ['Automation Engineering (document owner)', 'Maintains this SOP and the Deployment Guide; updates both whenever the underlying scripts change.'],
      ],
    },
  },
  { pageBreak: true },
];

module.exports = {
  TITLE_BLOCKS, DOC_CONTROL, SEC1_PURPOSE, SEC2_OVERVIEW, SEC3_GLOSSARY, SEC4_ROLES,
};
