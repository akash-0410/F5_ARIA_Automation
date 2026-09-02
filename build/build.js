const fs = require('fs');
const path = require('path');
const { Packer } = require('docx');
const {
  Document, render, numberingConfig, getDynamicNumberingConfigs, HeadingLevel,
} = require('./render.js');

const {
  TITLE_BLOCKS, DOC_CONTROL, SEC1_PURPOSE, SEC2_OVERVIEW, SEC3_GLOSSARY, SEC4_ROLES,
} = require('./content.js');
const { SEC5_NAMING, SEC6_PROVISIONING } = require('./content2.js');
const { SEC7_CONFIG, SEC8_BUGFIXES } = require('./content3.js');
const {
  SEC9_CHANGE_MGMT, SEC10_DEPLOYMENT_SUMMARY, SEC11_VERIFICATION, SEC12_RISKS,
  SEC13_ROLLBACK, SEC14_OPERATIONS, SEC15_SIGNOFF, SEC16_HISTORY,
} = require('./content4.js');

const allBlocks = [
  ...TITLE_BLOCKS,
  ...DOC_CONTROL,
  ...SEC1_PURPOSE,
  ...SEC2_OVERVIEW,
  ...SEC3_GLOSSARY,
  ...SEC4_ROLES,
  ...SEC5_NAMING,
  ...SEC6_PROVISIONING,
  ...SEC7_CONFIG,
  ...SEC8_BUGFIXES,
  ...SEC9_CHANGE_MGMT,
  ...SEC10_DEPLOYMENT_SUMMARY,
  ...SEC11_VERIFICATION,
  ...SEC12_RISKS,
  ...SEC13_ROLLBACK,
  ...SEC14_OPERATIONS,
  ...SEC15_SIGNOFF,
  ...SEC16_HISTORY,
];

const children = render(allBlocks);

const fullNumberingConfig = {
  config: [...numberingConfig.config, ...getDynamicNumberingConfigs()],
};

const doc = new Document({
  numbering: fullNumberingConfig,
  styles: {
    default: {
      document: { run: { font: 'Calibri', size: 22 } },
      heading1: { run: { font: 'Calibri', size: 32, bold: true, color: '1F3864' }, paragraph: { spacing: { before: 480, after: 200 } } },
      heading2: { run: { font: 'Calibri', size: 26, bold: true, color: '2E5B8A' }, paragraph: { spacing: { before: 320, after: 140 } } },
      heading3: { run: { font: 'Calibri', size: 24, bold: true, color: '2E5B8A' }, paragraph: { spacing: { before: 240, after: 100 } } },
    },
  },
  sections: [
    {
      properties: {
        page: {
          size: { width: 12240, height: 15840 }, // US Letter, DXA
          margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 },
        },
      },
      children,
    },
  ],
});

const outPath = path.join(__dirname, '..', 'SOP.docx');
Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync(outPath, buf);
  console.log('Wrote', outPath, buf.length, 'bytes');
}).catch(err => {
  console.error('BUILD FAILED:', err);
  process.exit(1);
});
