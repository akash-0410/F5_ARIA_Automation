// Shared mini-DSL renderer for building the SOP.docx with docx-js.
// Block types: h1, h2, h3, h4, p, code, ul, ol, table, pageBreak, spacer
const {
  Document, Paragraph, TextRun, HeadingLevel, Table, TableRow, TableCell,
  WidthType, ShadingType, BorderStyle, AlignmentType, PageBreak,
  LevelFormat, convertInchesToTwip,
} = require('docx');

const FONT_BODY = 'Calibri';
const FONT_CODE = 'Consolas';
const FONT_HEAD = 'Calibri';

const COLOR_ACCENT = '2E5B8A';   // deep steel blue, headings
const COLOR_WARN = 'B23A2F';     // warning/critical red-brown
const COLOR_MUTED = '5B6B7A';
const COLOR_CODE_BG = 'F2F4F7';
const COLOR_RULE = 'D7DEE6';

function h1(text) {
  return new Paragraph({
    text,
    heading: HeadingLevel.HEADING_1,
    spacing: { before: 480, after: 200 },
    border: { bottom: { color: COLOR_ACCENT, space: 4, style: BorderStyle.SINGLE, size: 8 } },
  });
}
function h2(text) {
  return new Paragraph({ text, heading: HeadingLevel.HEADING_2, spacing: { before: 320, after: 140 } });
}
function h3(text) {
  return new Paragraph({ text, heading: HeadingLevel.HEADING_3, spacing: { before: 240, after: 100 } });
}
function h4(text) {
  return new Paragraph({
    children: [new TextRun({ text, bold: true, italics: true, size: 22, font: FONT_BODY })],
    spacing: { before: 200, after: 80 },
  });
}

function p(text, opts = {}) {
  const runs = Array.isArray(text) ? text : [{ text }];
  return new Paragraph({
    children: runs.map(r => new TextRun({
      text: r.text, bold: !!r.bold, italics: !!r.italics, font: FONT_BODY, size: 22,
      color: r.color || undefined,
    })),
    spacing: { after: 160 },
    alignment: opts.center ? AlignmentType.CENTER : AlignmentType.LEFT,
  });
}

function note(text, kind = 'note') {
  const color = kind === 'warn' ? COLOR_WARN : COLOR_ACCENT;
  const label = kind === 'warn' ? 'IMPORTANT: ' : 'NOTE: ';
  return new Paragraph({
    children: [
      new TextRun({ text: label, bold: true, color, font: FONT_BODY, size: 22 }),
      new TextRun({ text, font: FONT_BODY, size: 22 }),
    ],
    spacing: { before: 100, after: 160 },
    border: {
      left: { color, space: 8, style: BorderStyle.SINGLE, size: 18 },
    },
    indent: { left: 120 },
  });
}

function code(lines) {
  return new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    borders: {
      top: { style: BorderStyle.SINGLE, size: 2, color: COLOR_RULE },
      bottom: { style: BorderStyle.SINGLE, size: 2, color: COLOR_RULE },
      left: { style: BorderStyle.SINGLE, size: 2, color: COLOR_RULE },
      right: { style: BorderStyle.SINGLE, size: 2, color: COLOR_RULE },
      insideHorizontal: { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' },
      insideVertical: { style: BorderStyle.NONE, size: 0, color: 'FFFFFF' },
    },
    rows: [
      new TableRow({
        children: [
          new TableCell({
            width: { size: 100, type: WidthType.PERCENTAGE },
            shading: { type: ShadingType.CLEAR, color: 'auto', fill: COLOR_CODE_BG },
            margins: { top: 120, bottom: 120, left: 160, right: 160 },
            children: lines.map(line => new Paragraph({
              children: [new TextRun({ text: line.length ? line : ' ', font: FONT_CODE, size: 19 })],
              spacing: { after: 0 },
            })),
          }),
        ],
      }),
    ],
  });
}

// Each ordered list gets its own numbering reference so numbering restarts
// at 1 for every separate `ol` block instead of continuing across the whole
// document. dynamicOlConfigs collects the extra numbering definitions that
// must be registered on the Document (see getDynamicNumberingConfigs()).
let olCounter = 0;
const dynamicOlConfigs = [];

function listParas(items, ordered) {
  let reference = 'ul-ref';
  if (ordered) {
    reference = `ol-ref-${olCounter++}`;
    dynamicOlConfigs.push({
      reference,
      levels: [
        { level: 0, format: LevelFormat.DECIMAL, text: '%1.', alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: convertInchesToTwip(0.35), hanging: convertInchesToTwip(0.2) } } } },
      ],
    });
  }
  return items.map((item, i) => new Paragraph({
    children: Array.isArray(item)
      ? item.map(r => new TextRun({ text: r.text, bold: !!r.bold, italics: !!r.italics, font: FONT_BODY, size: 22 }))
      : [new TextRun({ text: item, font: FONT_BODY, size: 22 })],
    numbering: { reference, level: 0 },
    spacing: { after: 80 },
  }));
}

function ul(items) { return listParas(items, false); }
function ol(items) { return listParas(items, true); }
function getDynamicNumberingConfigs() { return dynamicOlConfigs; }

function table({ headers, rows, widths }) {
  const totalPct = 100;
  const colWidths = widths || headers.map(() => Math.floor(totalPct / headers.length));
  const dxaTotal = convertInchesToTwip(9.0); // usable width approx for letter w/ 1in margins
  const dxaWidths = colWidths.map(pctToDxa => Math.floor((pctToDxa / totalPct) * dxaTotal));

  const headerRow = new TableRow({
    tableHeader: true,
    children: headers.map((htext, i) => new TableCell({
      width: { size: dxaWidths[i], type: WidthType.DXA },
      shading: { type: ShadingType.CLEAR, color: 'auto', fill: COLOR_ACCENT },
      margins: { top: 80, bottom: 80, left: 100, right: 100 },
      children: [new Paragraph({
        children: [new TextRun({ text: htext, bold: true, color: 'FFFFFF', font: FONT_BODY, size: 20 })],
      })],
    })),
  });

  const bodyRows = rows.map((row, rIdx) => new TableRow({
    children: row.map((cellText, i) => new TableCell({
      width: { size: dxaWidths[i], type: WidthType.DXA },
      shading: rIdx % 2 === 1 ? { type: ShadingType.CLEAR, color: 'auto', fill: 'F7F9FB' } : undefined,
      margins: { top: 70, bottom: 70, left: 100, right: 100 },
      children: (Array.isArray(cellText) ? cellText : [cellText]).map(part => {
        if (typeof part === 'string') {
          return new Paragraph({ children: [new TextRun({ text: part, font: FONT_BODY, size: 19 })] });
        }
        return new Paragraph({
          children: [new TextRun({ text: part.text, font: part.code ? FONT_CODE : FONT_BODY, size: 19, bold: !!part.bold, color: part.color })],
        });
      }),
    })),
  }));

  return new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    borders: {
      top: { style: BorderStyle.SINGLE, size: 2, color: COLOR_RULE },
      bottom: { style: BorderStyle.SINGLE, size: 2, color: COLOR_RULE },
      left: { style: BorderStyle.SINGLE, size: 2, color: COLOR_RULE },
      right: { style: BorderStyle.SINGLE, size: 2, color: COLOR_RULE },
      insideHorizontal: { style: BorderStyle.SINGLE, size: 2, color: COLOR_RULE },
      insideVertical: { style: BorderStyle.SINGLE, size: 2, color: COLOR_RULE },
    },
    rows: [headerRow, ...bodyRows],
  });
}

function pageBreak() {
  return new Paragraph({ children: [new PageBreak()] });
}
function spacer(size = 120) {
  return new Paragraph({ text: '', spacing: { after: size } });
}

// Render a block-array (mini-DSL) into an array of docx elements
function render(blocks) {
  const out = [];
  for (const b of blocks) {
    if (b.h1) out.push(h1(b.h1));
    else if (b.h2) out.push(h2(b.h2));
    else if (b.h3) out.push(h3(b.h3));
    else if (b.h4) out.push(h4(b.h4));
    else if (b.p) out.push(p(b.p, b.opts || {}));
    else if (b.note) out.push(note(b.note, b.kind));
    else if (b.code) out.push(code(b.code));
    else if (b.ul) out.push(...ul(b.ul));
    else if (b.ol) out.push(...ol(b.ol));
    else if (b.table) out.push(table(b.table));
    else if (b.pageBreak) out.push(pageBreak());
    else if (b.spacer !== undefined) out.push(spacer(b.spacer));
  }
  return out;
}

const numberingConfig = {
  config: [
    {
      reference: 'ul-ref',
      levels: [
        { level: 0, format: LevelFormat.BULLET, text: '•', alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: convertInchesToTwip(0.35), hanging: convertInchesToTwip(0.2) } } } },
      ],
    },
  ],
};

module.exports = {
  Document, Paragraph, TextRun, HeadingLevel, WidthType,
  render, h1, h2, h3, h4, p, note, code, ul, ol, table, pageBreak, spacer,
  numberingConfig, getDynamicNumberingConfigs, COLOR_ACCENT, COLOR_WARN, COLOR_MUTED, FONT_BODY, FONT_CODE,
};
