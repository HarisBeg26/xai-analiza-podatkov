import fs from "node:fs/promises";
import path from "node:path";
import { Workbook, SpreadsheetFile } from "@oai/artifact-tool";

const baseDir = path.resolve("C:/Users/vunja/Desktop/XAI-Master projekt/Analiza-Podatkov");
const outputDir = path.join(baseDir, "analysis_outputs");

const summary = JSON.parse(await fs.readFile(path.join(outputDir, "summary.json"), "utf8"));
const shortCodes = JSON.parse(await fs.readFile(path.join(outputDir, "short_codes_review.json"), "utf8"));
const suspiciousCodes = JSON.parse(await fs.readFile(path.join(outputDir, "suspicious_codes.json"), "utf8"));
const weeklyCounts = JSON.parse(await fs.readFile(path.join(outputDir, "weekly_counts.json"), "utf8"));
const participantWeekCounts = JSON.parse(
  await fs.readFile(path.join(outputDir, "participant_week_counts.json"), "utf8"),
);
const excludedCases = JSON.parse(await fs.readFile(path.join(outputDir, "excluded_cases.json"), "utf8"));
const surveyCsv = await fs.readFile(path.join(outputDir, "survey_marked.csv"), "utf8");

const workbook = await Workbook.fromCSV(surveyCsv, { sheetName: "Oznaceni podatki" });

function columnLetter(index) {
  let current = index;
  let result = "";
  while (current > 0) {
    const remainder = (current - 1) % 26;
    result = String.fromCharCode(65 + remainder) + result;
    current = Math.floor((current - 1) / 26);
  }
  return result;
}

function cellRef(row, col) {
  return `${columnLetter(col)}${row}`;
}

function rangeRef(startRow, startCol, rowCount, colCount) {
  const endRow = startRow + rowCount - 1;
  const endCol = startCol + colCount - 1;
  return `${cellRef(startRow, startCol)}:${cellRef(endRow, endCol)}`;
}

function makeMatrixFromObjects(rows) {
  if (!rows.length) {
    return [["Ni podatkov"]];
  }
  const headers = Object.keys(rows[0]);
  const matrix = [headers];
  for (const row of rows) {
    matrix.push(headers.map((key) => row[key] ?? ""));
  }
  return matrix;
}

function styleHeader(sheet, startRow, startCol, colCount) {
  const headerRange = sheet.getRange(rangeRef(startRow, startCol, 1, colCount));
  headerRange.format = {
    fill: { type: "solid", color: "#DCE6F2" },
    font: { name: "Calibri", size: 11, bold: true, color: "#16324F" },
    borders: { preset: "outside", style: "thin", color: "#B7C4D3" },
    horizontalAlignment: "center",
    verticalAlignment: "center",
    wrapText: true,
  };
}

function styleBody(sheet, startRow, startCol, rowCount, colCount, wrap = false) {
  const bodyRange = sheet.getRange(rangeRef(startRow, startCol, rowCount, colCount));
  bodyRange.format = {
    font: { name: "Calibri", size: 11, color: "#1F2937" },
    borders: { preset: "outside", style: "thin", color: "#E5E7EB" },
    verticalAlignment: "top",
    wrapText: wrap,
  };
}

function addTable(sheet, startRow, startCol, matrix, { wrapBody = false } = {}) {
  const rows = matrix.length;
  const cols = matrix[0].length;
  sheet.getRange(rangeRef(startRow, startCol, rows, cols)).values = matrix;
  styleHeader(sheet, startRow, startCol, cols);
  if (rows > 1) {
    styleBody(sheet, startRow + 1, startCol, rows - 1, cols, wrapBody);
  }
  return { rows, cols };
}

const mainSheet = workbook.worksheets.getItem("Oznaceni podatki");
mainSheet.freezePanes.freezeRows(1);
mainSheet.freezePanes.freezeColumns(5);

const surveyHeaderCount = surveyCsv.split(/\r?\n/, 1)[0].split(",").length;
styleHeader(mainSheet, 1, 1, surveyHeaderCount);
mainSheet.getRange(`A:${columnLetter(surveyHeaderCount)}`).format.autofitColumns();
mainSheet.getRange("A:Z").format.wrapText = false;

const summarySheet = workbook.worksheets.add("Povzetek");
summarySheet.getRange("A1:F1").merge();
summarySheet.getRange("A1").values = [["Analiza ankete - povzetek"]];
summarySheet.getRange("A1").format = {
  fill: { type: "solid", color: "#1F4E78" },
  font: { name: "Calibri", size: 16, bold: true, color: "#FFFFFF" },
  horizontalAlignment: "left",
  verticalAlignment: "center",
};

summarySheet.getRange("A3").values = [["Glavne metrike"]];
summarySheet.getRange("A3").format.font = { name: "Calibri", size: 12, bold: true, color: "#16324F" };

const metricRows = [
  ["Metrika", "Vrednost"],
  ["Skupno vrstic brez opisne vrstice", summary.metrics.skupno_vrstic_brez_opisne_vrstice],
  ["Status = 6 skupaj", summary.metrics.status_6_skupaj],
  ["Testne vrstice skupaj", summary.metrics.test_vrstice_skupaj],
  ["Veljavni odgovori (status 6, brez test)", summary.metrics.veljavni_odgovori_osnovno_status6_brez_test],
  ["Veljavni odgovori z razreseno uradno kodo", summary.metrics.veljavni_odgovori_z_uradno_ali_razreseno_kodo],
  ["Unikatni veljavni udelezenci", summary.metrics.unikatni_veljavni_udelezenci_po_uradni_8_mestni_kodi],
  ["Pravilno vnesene 8-mestne uradne kode", summary.metrics.unikatne_pravilno_vnesene_8_mestne_uradne_kode],
  ["4-mestne kode med veljavnimi", summary.metrics["4_mestne_kode_med_veljavnimi"]],
  ["5-mestne kode med veljavnimi", summary.metrics["5_mestne_kode_med_veljavnimi"]],
  ["7-mestne kode med veljavnimi", summary.metrics["7_mestne_kode_med_veljavnimi"]],
  ["Sumljive 8-mestne kode izven seznama", summary.metrics.sumljive_8_mestne_kode_izven_uradnega_seznama],
];
addTable(summarySheet, 4, 1, metricRows);

summarySheet.getRange("D3").values = [["Razresitev kod med veljavnimi odgovori"]];
summarySheet.getRange("D3").format.font = { name: "Calibri", size: 12, bold: true, color: "#16324F" };
const resolutionRows = [["Nacin razresitve", "St. vrstic"]];
for (const [key, value] of Object.entries(summary.code_resolution_counts_valid_loose)) {
  resolutionRows.push([key, value]);
}
addTable(summarySheet, 4, 4, resolutionRows);

summarySheet.getRange("A17").values = [["Tedenska porazdelitev"]];
summarySheet.getRange("A17").format.font = { name: "Calibri", size: 12, bold: true, color: "#16324F" };
const weeklyTable = [["ISO leto", "ISO teden", "Veljavne vrstice", "Unikatni udelezeni", "Od", "Do"]];
for (const row of weeklyCounts) {
  weeklyTable.push([
    row.iso_year,
    row.iso_week,
    row.valid_rows,
    row.unique_participants,
    row.date_min,
    row.date_max,
  ]);
}
addTable(summarySheet, 18, 1, weeklyTable);

summarySheet.charts.add("bar", {
  title: "Udelezenci po tednih",
  titleTextStyle: { fontSize: 14, bold: true },
  categories: weeklyCounts.map((row) => `W${row.iso_week}`),
  series: [
    {
      name: "Unikatni udelezeni",
      values: weeklyCounts.map((row) => row.unique_participants),
    },
  ],
  hasLegend: false,
  barOptions: { direction: "column", grouping: "clustered", gapWidth: 60 },
  dataLabels: { showValue: true },
  from: { row: 2, col: 7 },
  extent: { widthPx: 430, heightPx: 280 },
});

summarySheet.freezePanes.freezeRows(3);
summarySheet.getRange("A:J").format.autofitColumns();

const shortCodesSheet = workbook.worksheets.add("Kratke kode");
shortCodesSheet.getRange("A1").values = [["Pregled kratko vnesenih kod"]];
shortCodesSheet.getRange("A1").format.font = { name: "Calibri", size: 14, bold: true, color: "#16324F" };
const shortCodeMatrix = makeMatrixFromObjects(shortCodes);
addTable(shortCodesSheet, 3, 1, shortCodeMatrix, { wrapBody: true });
shortCodesSheet.freezePanes.freezeRows(3);
shortCodesSheet.getRange("A:I").format.autofitColumns();

const suspiciousSheet = workbook.worksheets.add("Sumljive kode");
suspiciousSheet.getRange("A1").values = [["Kode za rocni pregled"]];
suspiciousSheet.getRange("A1").format.font = { name: "Calibri", size: 14, bold: true, color: "#16324F" };
const suspiciousMatrix = makeMatrixFromObjects(suspiciousCodes);
addTable(suspiciousSheet, 3, 1, suspiciousMatrix, { wrapBody: true });
suspiciousSheet.freezePanes.freezeRows(3);
suspiciousSheet.getRange("A:G").format.autofitColumns();

const participantWeekSheet = workbook.worksheets.add("Odgovori po tednih");
participantWeekSheet.getRange("A1").values = [["Stevilo odgovorov po udelezencu in tednu"]];
participantWeekSheet.getRange("A1").format.font = {
  name: "Calibri",
  size: 14,
  bold: true,
  color: "#16324F",
};
const participantWeekMatrix = makeMatrixFromObjects(participantWeekCounts);
addTable(participantWeekSheet, 3, 1, participantWeekMatrix);
participantWeekSheet.freezePanes.freezeRows(3);
participantWeekSheet.freezePanes.freezeColumns(1);
participantWeekSheet.getRange("A:H").format.autofitColumns();

const excludedSheet = workbook.worksheets.add("Izloceni primeri");
excludedSheet.getRange("A1").values = [[
  "Testni primeri, status < 6 in vnosi brez 8-mestne kode",
]];
excludedSheet.getRange("A1").format.font = {
  name: "Calibri",
  size: 14,
  bold: true,
  color: "#16324F",
};
const excludedMatrix = makeMatrixFromObjects(excludedCases);
addTable(excludedSheet, 3, 1, excludedMatrix, { wrapBody: true });
excludedSheet.freezePanes.freezeRows(3);
excludedSheet.freezePanes.freezeColumns(1);
excludedSheet.getRange("A:M").format.autofitColumns();

const outputPath = path.join(outputDir, "anketa191776-2026-04-10_analiza.xlsx");
const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(outputPath);

console.log(outputPath);
