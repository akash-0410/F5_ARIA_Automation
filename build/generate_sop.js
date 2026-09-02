const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, ImageRun,
  Table, TableRow, TableCell, WidthType, ShadingType, BorderStyle,
  AlignmentType, PageBreak, ExternalHyperlink, LevelFormat, convertInchesToTwip,
} = require("docx");

const SHOT_DIR = path.join(__dirname, "..", "screenshots");
const OUT = path.join(__dirname, "..", "SOP.docx");

function img(filename, widthPx) {
  const data = fs.readFileSync(path.join(SHOT_DIR, filename));
  const w = widthPx || 600;
  const h = Math.round(w * (726 / 1568));
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 120, after: 60 },
    children: [
      new ImageRun({
        data,
        type: "jpg",
        transformation: { width: w, height: h },
      }),
    ],
  });
}

function caption(text) {
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 240 },
    children: [new TextRun({ text, italics: true, size: 18, color: "5B6472" })],
  });
}

function h1(text) {
  return new Paragraph({ heading: HeadingLevel.HEADING_1, spacing: { before: 400, after: 160 }, text });
}
function h2(text) {
  return new Paragraph({ heading: HeadingLevel.HEADING_2, spacing: { before: 320, after: 120 }, text });
}
function h3(text) {
  return new Paragraph({ heading: HeadingLevel.HEADING_3, spacing: { before: 240, after: 100 }, text });
}
function p(runsOrText, opts) {
  const children = typeof runsOrText === "string" ? [new TextRun(runsOrText)] : runsOrText;
  return new Paragraph({ spacing: { after: 160 }, children, ...(opts || {}) });
}
function code(text) {
  return new TextRun({ text, font: "Consolas", size: 20, color: "8A3B00" });
}
function bold(text) {
  return new TextRun({ text, bold: true });
}
function italic(text) {
  return new TextRun({ text, italics: true });
}

function bullet(text, level) {
  return new Paragraph({
    text,
    bullet: { level: level || 0 },
    spacing: { after: 90 },
  });
}
function numbered(text, refKey) {
  return new Paragraph({
    text,
    numbering: { reference: refKey || "default-num", level: 0 },
    spacing: { after: 90 },
  });
}

const NUM_REFS = [
  "default-num", "sec0", "sec1", "sec2", "sec3", "sec4", "sec4b",
  "sec6", "op1", "op2", "op3",
];

function warnBox(lines) {
  return new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    borders: {
      top: { style: BorderStyle.SINGLE, size: 4, color: "E8C468" },
      bottom: { style: BorderStyle.SINGLE, size: 4, color: "E8C468" },
      left: { style: BorderStyle.SINGLE, size: 4, color: "E8C468" },
      right: { style: BorderStyle.SINGLE, size: 4, color: "E8C468" },
    },
    rows: [
      new TableRow({
        children: [
          new TableCell({
            shading: { type: ShadingType.CLEAR, fill: "FFF6E5" },
            margins: { top: 160, bottom: 160, left: 200, right: 200 },
            children: lines.map((l, i) => new Paragraph({
              spacing: { after: i === lines.length - 1 ? 0 : 80 },
              children: l,
            })),
          }),
        ],
      }),
    ],
  });
}

function simpleTable(headerRow, rows, colWidths) {
  const totalWidth = 9000;
  const widths = colWidths || headerRow.map(() => Math.floor(totalWidth / headerRow.length));
  const mkCell = (text, isHeader, width) => new TableCell({
    width: { size: width, type: WidthType.DXA },
    shading: isHeader ? { type: ShadingType.CLEAR, fill: "F4F1EA" } : undefined,
    margins: { top: 80, bottom: 80, left: 100, right: 100 },
    children: [new Paragraph({ children: [new TextRun({ text, bold: !!isHeader, size: 20 })] })],
  });
  return new Table({
    width: { size: totalWidth, type: WidthType.DXA },
    columnWidths: widths,
    rows: [
      new TableRow({ tableHeader: true, children: headerRow.map((t, i) => mkCell(t, true, widths[i])) }),
      ...rows.map(r => new TableRow({ children: r.map((t, i) => mkCell(t, false, widths[i])) })),
    ],
  });
}

const doc = new Document({
  numbering: {
    config: NUM_REFS.map((reference) => ({
      reference,
      levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.START,
        style: { paragraph: { indent: { left: convertInchesToTwip(0.35), hanging: convertInchesToTwip(0.25) } } } }],
    })),
  },
  sections: [
    {
      properties: {
        page: {
          size: { width: 12240, height: 15840 },
          margins: { top: 1080, bottom: 1080, left: 1080, right: 1080 },
        },
      },
      children: [
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { after: 60 },
          children: [new TextRun({ text: "F5 Automation — Setup & Operations SOP", bold: true, size: 40 })],
        }),
        new Paragraph({
          alignment: AlignmentType.CENTER,
          spacing: { after: 480 },
          children: [new TextRun({
            text: "VMware Aria Automation 8.x · fresh client build, click by click, with screenshots · covers first-time setup and day-2 operator tasks",
            italics: true, size: 22, color: "5B6472",
          })],
        }),

        h1("Part 1 — First-time setup"),
        p([new TextRun("This section mirrors "), code("DEPLOYMENT_GUIDE.md"), new TextRun(" in the package, with screenshots added. A handful of screens (the vRO wrapper's General tab, the Custom Resource form, the blueprint editor, and the Custom Form editor) are described in full text detail but aren't screenshotted in this pass — see the note at the end of this document.")]),

        h2("0. Logging in and finding your way around"),
        p("Aria Automation bundles four sub-apps behind one login:"),
        bullet([new TextRun({ text: "Assembler", bold: true }), new TextRun(" — build ABX actions, Custom Resources, and Cloud Templates. Most of this guide happens here.")].reduce((a,b)=>a,null) || "Assembler — build ABX actions, Custom Resources, and Cloud Templates. Most of this guide happens here."),
        bullet("Orchestrator (\"vRO\") — a separate app with its own JavaScript actions, used for the 15 wrapper scripts."),
        bullet("Service Broker — publish the finished template to a catalog, and where the Custom Form lives."),
        bullet("Pipelines — not used in this build."),
        numbered("Go to https://<your-vra-host>/automation/. Log in with a Cloud Assembly Administrator account.", "sec0"),
        numbered("You land on \"My Services\" with four tiles: Assembler, Orchestrator, Pipelines, Service Broker.", "sec0"),
        numbered("Click a tile to enter that app. Each has its own top tab bar and a left sidebar that changes with the selected top tab.", "sec0"),
        warnBox([[bold("Navigation tip: "), new TextRun("always reach a screen by clicking through tabs and the sidebar from the launcher, rather than pasting a deep-link URL into the address bar. Deep-linking occasionally leaves the app showing a stale page for the URL shown. If a page ever looks wrong, click a top tab away and back, or open a fresh tab from the launcher.")]]),

        h2("1. Finding or creating the Project, and finding the Project ID"),
        numbered("Assembler > Infrastructure tab > left sidebar, under Administration, Projects.", "sec1"),
        img("01_projects_list.jpg"),
        caption("Fig. 1 — Projects list (Assembler > Infrastructure > Projects). The lab has two: F5-Automation and Test_f5."),
        numbered("To create one: + NEW, name it, add Administrators/Members on the Users tab, save. To use an existing one: click its card.", "sec1"),
        numbered("Click OPEN on the project's card.", "sec1"),
        warnBox([
          [bold("Where is the Project ID? "), new TextRun("It isn't printed as a labeled field on the Summary page. It's in the browser's address bar once the project is open — look for a long hyphenated hex string after "), code("/projects/edit/"), new TextRun(", e.g.:")],
          [code(".../provisioning-ui;ash=%2Fprojects%2Fedit%2Fd347d2fd-4e27-4a0d-b144-f5262d7a70a1")],
          [new TextRun("Everything after "), code("edit/"), new TextRun(" is the Project ID. You'll need it for "), code("bootstrap/config.json"), new TextRun(".")],
        ]),
        img("02_project_id_in_url.jpg"),
        caption("Fig. 2 — The project's Summary page. The ID is not shown here on the page — check your browser's own URL bar while this screen is open."),

        h2("2. Creating the 19 ABX Extensibility Actions"),
        numbered("Assembler > Extensibility tab > left sidebar > Actions.", "sec2"),
        img("03_actions_list.jpg"),
        caption("Fig. 3 — Extensibility > Actions. The lab's live list (already populated with all 19); yours starts empty."),
        numbered("Click + NEW.", "sec2"),
        img("04_new_action_dialog.jpg"),
        caption("Fig. 4 — The New Action dialog. Name must exactly match the script filename (without .py)."),
        numbered("Type the project name into Project — it autocompletes.", "sec2"),
        img("05_new_action_project_picker.jpg"),
        caption("Fig. 5 — Selecting the project from the autocomplete dropdown."),
        numbered("Click NEXT. You land on the action editor: code on the left, settings on the right.", "sec2"),
        img("06_action_editor_main.jpg"),
        caption("Fig. 6 — Action editor layout (Type/Runtime dropdowns top-left; Main function, Dependency, Default inputs on the right). Shown with placeholder starter code — paste in the real script here."),
        numbered("Set runtime to Python 3.10 (or closest available). Delete the placeholder code, paste in the matching file from scripts_lab_raw/ (or scripts/f5_create_virtual_server.py).", "sec2"),
        numbered("Main function: handler. Dependency: requests.", "sec2"),
        numbered("Default inputs: leave empty for now (added in Section 3 below).", "sec2"),
        numbered("SAVE, optionally TEST, then CLOSE and repeat for all 19 names (full list in DEPLOYMENT_GUIDE.md Section 2.2).", "sec2"),
        warnBox([[bold("Record each action's ID "), new TextRun("from the browser URL as you save it (same trick as the Project ID) — you'll need all 19 in Section 4 to point the matching vRO wrapper at the right action. "), code("bootstrap/vra_bootstrap.py --apply"), new TextRun(" can do this for you (unverified — see that folder's README).")]]),
        warnBox([[bold("Naming exception: "), new TextRun("the wrapper you build in Section 4 as "), code("f5_list_monitors"), new TextRun(" should call the ABX action "), code("f5_list_monitors"), new TextRun(", not "), code("f5_list_monitor_types"), new TextRun(" — see "), code("platform_config_raw/finding_monitor_type_vs_monitors.md"), new TextRun(" for the full confirmed audit.")]]),

        h2("3. Default Inputs, Secret Inputs, and Action Constants"),
        p("Do this after all 19 actions exist."),
        simpleTable(
          ["Needs f5_username + F5_SHARED_PASSWORD", "Needs F5_VIP_SUBNET_REGISTRY (Action Constant)", "Needs F5_DEVICE_REGISTRY (Action Constant)"],
          [["f5_create_virtual_server, f5_read_virtual_server, f5_delete_virtual_server, f5_update_pool_settings, f5_update_backend_nodes, f5_list_nodes, f5_list_nodes_grid, and every live-device f5_list_* action", "f5_create_virtual_server only", "f5_list_clusters only"]],
        ),
        p(""),
        numbered("Open the action > find Default inputs on the right panel (the same section shown empty in Fig. 6).", "sec3"),
        numbered("Add a row: Type = Default, Name = f5_username, Value = the F5 API service account username.", "sec3"),
        numbered("Add a row: Type = Secret, Name = F5_SHARED_PASSWORD. This opens/creates a vRA Secret rather than storing plaintext.", "sec3"),
        numbered("Save. Repeat for every action in the left column above.", "sec3"),
        p([bold("Action Constant #1: "), new TextRun("Extensibility > Actions > Action Constants sub-tab > + NEW > Name F5_VIP_SUBNET_REGISTRY, Value a JSON map of F5 host to VIP subnet CIDR (see DEPLOYMENT_GUIDE.md Section 4.3.1 for the exact JSON shape). Attach to f5_create_virtual_server.")]),
        p([bold("Action Constant #2: "), new TextRun("same sub-tab > + NEW > Name F5_DEVICE_REGISTRY, Value a JSON map keyed by Location then Environment listing each F5 device's label and host (see DEPLOYMENT_GUIDE.md Section 4.3.2). Attach to f5_list_clusters. This is the actual F5 device inventory feeding the \"F5 Cluster\" dropdown — easy to miss since no wrapper or Custom Form field references it by name, but without it that dropdown silently returns zero options.")]),
        warnBox([[bold("Known risk to raise with the client: "), new TextRun("one shared username/password is used for every F5 device. There's no per-cluster credential map today, despite a comment in f5_list_nodes.py referencing one — that pattern was never implemented.")]]),

        h2("4. vRO Orchestrator: the module and 15 wrapper actions"),
        p("The Custom Form doesn't call ABX actions directly — it calls these 15 JavaScript \"wrapper\" actions in Orchestrator, which call the ABX actions above."),
        numbered("From the launcher, click Orchestrator (a separate app, own left sidebar: Dashboard, Workflows, Actions, Configurations).", "sec4"),
        numbered("Library > Actions > New Action. In Module, type com.f5.automation — typing it fresh and saving the first action creates the module automatically; there's no separate \"create module\" button.", "sec4"),
        numbered("Name the first one f5_vra_run_action (create this first — every other wrapper except f5_generate_deployment_name calls it internally). Runtime: JavaScript. Paste in wrapper_scripts_raw/f5_vra_run_action.js.", "sec4"),
        numbered("On the General tab, add the tag com.f5.automation. This is separate from the Module field — both are needed.", "sec4"),
        numbered("Save, then repeat for the other 14 files in wrapper_scripts_raw/. Before saving each, replace its hardcoded ACTION_ID with the real ID you recorded in Section 2.", "sec4"),
        img("07_vro_action_script_tab.jpg"),
        caption("Fig. 7 — A wrapper action's Script tab (shown live: f5_list_clusters, inputs location/environment, return type Array of string). The General tab (Module + Tags fields) is a separate tab next to this one."),
        h3("Two Configuration Elements (create by hand)"),
        numbered("F5-Automation-Credentials (folder web-root) — attribute vraRefreshToken (SecureString): a long-lived vRA refresh token for a service account. Never write this value to a file.", "sec4b"),
        numbered("F5-Automation / DeploymentNaming — attribute sequenceCounters (Properties, empty): self-initializes on first use.", "sec4b"),
        p([bold("Verify: "), new TextRun("Library > Actions > filter Tags: com.f5.automation → 15 actions. Run f5_list_locations manually with no inputs as a smoke test.")]),

        h2("5. Custom Resource, Blueprint, and Custom Form"),
        p([bold("Custom Resource "), new TextRun("(Design > Custom Resources > New): Resource Type Custom.F5.VirtualServer, paste the schema from platform_config_raw/custom_resource_F5.VirtualServer.md, wire lifecycle actions and the three Day-2 actions, activate, scope to your project.")]),
        p([bold("Blueprint "), new TextRun("(Design > Templates > New > Code editor): paste platform_config_raw/blueprint_F5-Virtual-Server.yaml, confirm every ${input.*} matches an inputs: entry, Test, publish a version.")]),
        p([bold("Custom Form "), new TextRun("(Service Broker > Content & Policies > Content > expand the template's row > enable Custom Form): bind each field's External source to the matching vRO wrapper — full field-by-field table is in DEPLOYMENT_GUIDE.md Section 8.")]),
        warnBox([[bold("Decide with the client "), new TextRun("whether to keep the blueprint's monitorType/monitorInterval/monitorTimeout inputs and the Custom Resource's pool.monitor_type field — they're not exercised by any live code path today (see finding_monitor_type_vs_monitors.md).")]]),

        h2("6. Publish and verify"),
        numbered("Service Broker > Content Sources > sync your project's content source.", "sec6"),
        numbered("Content & Policies > Content > confirm Custom Request Form shows Enabled.", "sec6"),
        numbered("Entitle the right project(s)/users.", "sec6"),
        numbered("Submit one real test request end to end against a non-production F5 device.", "sec6"),
        numbered("Only then, move to Part 2 below with your operators.", "sec6"),

        new Paragraph({ children: [new PageBreak()] }),
        h1("Part 2 — Day-2 operations"),
        p("For the deploying engineer using the published catalog item day to day."),

        h2("1. Requesting a new virtual server"),
        numbered("Service Broker > Catalog > find the F5 Virtual Server item > Request.", "op1"),
        numbered("Fill the form top to bottom — each dropdown cascades from the ones above it (Location → Environment Type → F5 Cluster → everything else).", "op1"),
        numbered("Leave Virtual IP Address blank (or \"auto\") to auto-assign from the cluster's configured VIP subnet.", "op1"),
        numbered("Submit. Track progress under Assembler > Activity > Requests, or the deployment's own Events tab.", "op1"),

        h2("2. Updating health monitor / load balancing"),
        numbered("Open the deployed resource.", "op2"),
        numbered("Resource actions menu > Update Health Monitor / Load Balancing.", "op2"),
        numbered("This only touches the pool's monitor and load-balancing method — it does not re-evaluate the virtual server, VIP, or existing pool members.", "op2"),

        h2("3. Updating backend nodes"),
        numbered("Resource actions menu > Update Backend Nodes / Pool Members.", "op3"),
        numbered("Add, remove, or change nodes in the grid. Every row needs a Port.", "op3"),

        h2("4. Resyncing from the F5 device"),
        p("Resource actions menu > Resync from F5 Device — a read-only refresh of the resource's recorded state from what's actually configured on the device."),

        h2("5. Deleting a virtual server"),
        p("Deployment > Delete. This removes the virtual server for that deployment only — it leaves the shared pool and nodes untouched."),

        h2("6. Known risks and troubleshooting"),
        bullet("Shared F5 credentials: one username/password for every F5 device (see Part 1, Section 3)."),
        bullet("Health Monitor field: picks an existing monitor already configured on the device (via f5_list_monitors) — it does not create a new monitor type."),
        bullet("A cascading dropdown is empty: check Orchestrator > Activity > Action Runs for the backing wrapper's most recent run and error message; confirm the refresh token hasn't expired. If it's specifically the F5 Cluster dropdown, also confirm F5_DEVICE_REGISTRY (Part 1, Section 3) is populated and still attached to f5_list_clusters — that's the one Action Constant this dropdown depends on."),
        bullet("Deployment Name sequence looks wrong: the counter lives in the F5-Automation / DeploymentNaming Configuration Element's sequenceCounters attribute — it's per Location + Environment Type, not global."),

        new Paragraph({ spacing: { before: 400 }, children: [new TextRun({
          text: "See DEPLOYMENT_GUIDE.md for the same setup content in Markdown, and platform_config_raw/ for the underlying audit findings referenced throughout. A follow-up screenshot pass can add the Custom Resource form, blueprint editor, and Custom Form editor screens once the source lab environment is available again.",
          italics: true, size: 18, color: "5B6472",
        })] }),
      ],
    },
  ],
});

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync(OUT, buf);
  console.log("Wrote", OUT, buf.length, "bytes");
});
