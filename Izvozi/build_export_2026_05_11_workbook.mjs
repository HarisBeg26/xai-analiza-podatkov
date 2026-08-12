import fs from "node:fs/promises";
import path from "node:path";
import { Workbook, SpreadsheetFile } from "@oai/artifact-tool";

const baseDir = path.resolve(
  "C:/Users/vunja/Desktop/XAI-Master projekt/Analiza-Podatkov/Izvozi/analysis_outputs_2026_05_11",
);

async function latestMatching(regex) {
  const entries = await fs.readdir(baseDir, { withFileTypes: true });
  const matches = entries
    .filter((entry) => entry.isFile() && regex.test(entry.name))
    .map((entry) => entry.name)
    .sort();
  return matches.at(-1);
}

const datasetFile = await latestMatching(/^anketa191776-2026-05-11_dataset_analiza.*\.csv$/);
const summaryFile = await latestMatching(/^summary.*\.json$/);
const participantSummaryFile = await latestMatching(/^participant_summary.*\.json$/);
const participantWeekMatrixFile = await latestMatching(/^participant_week_matrix.*\.json$/);

const datasetCsv = await fs.readFile(path.join(baseDir, datasetFile), "utf8");
const summary = JSON.parse(await fs.readFile(path.join(baseDir, summaryFile), "utf8"));
const participantSummary = JSON.parse(
  await fs.readFile(path.join(baseDir, participantSummaryFile), "utf8"),
);
const participantWeekMatrix = JSON.parse(
  await fs.readFile(path.join(baseDir, participantWeekMatrixFile), "utf8"),
);

const workbook = await Workbook.fromCSV(datasetCsv, { sheetName: "Podatki analiza" });

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

function styleHeader(sheet, startRow, startCol, colCount) {
  const range = sheet.getRange(rangeRef(startRow, startCol, 1, colCount));
  range.format = {
    fill: { type: "solid", color: "#DCE6F2" },
    font: { name: "Calibri", size: 11, bold: true, color: "#16324F" },
    borders: { preset: "outside", style: "thin", color: "#B7C4D3" },
    horizontalAlignment: "center",
    verticalAlignment: "center",
    wrapText: true,
  };
}

function styleBody(sheet, startRow, startCol, rowCount, colCount, wrap = false) {
  if (rowCount <= 0 || colCount <= 0) return;
  const range = sheet.getRange(rangeRef(startRow, startCol, rowCount, colCount));
  range.format = {
    font: { name: "Calibri", size: 11, color: "#1F2937" },
    borders: { preset: "outside", style: "thin", color: "#E5E7EB" },
    verticalAlignment: "top",
    wrapText: wrap,
  };
}

function makeMatrixFromObjects(rows) {
  if (!rows.length) {
    return [["Ni podatkov"]];
  }
  const headers = Object.keys(rows[0]);
  return [headers, ...rows.map((row) => headers.map((key) => row[key] ?? ""))];
}

function addTable(sheet, startRow, startCol, matrix, wrapBody = false) {
  const rows = matrix.length;
  const cols = matrix[0].length;
  sheet.getRange(rangeRef(startRow, startCol, rows, cols)).values = matrix;
  styleHeader(sheet, startRow, startCol, cols);
  styleBody(sheet, startRow + 1, startCol, rows - 1, cols, wrapBody);
}

const dataSheet = workbook.worksheets.getItem("Podatki analiza");
const datasetHeaderCount = datasetCsv.split(/\r?\n/, 1)[0].split(",").length;
styleHeader(dataSheet, 1, 1, datasetHeaderCount);
dataSheet.freezePanes.freezeRows(1);
dataSheet.freezePanes.freezeColumns(8);
dataSheet.getRange(`A:${columnLetter(datasetHeaderCount)}`).format.autofitColumns();

const summarySheet = workbook.worksheets.add("Povzetek");
summarySheet.getRange("A1:F1").merge();
summarySheet.getRange("A1").values = [["Analiza izvoza 2026-05-11"]];
summarySheet.getRange("A1").format = {
  fill: { type: "solid", color: "#1F4E78" },
  font: { name: "Calibri", size: 16, bold: true, color: "#FFFFFF" },
  horizontalAlignment: "left",
};

const metricRows = [
  ["Metrika", "Vrednost"],
  ["Veljavni odgovori (status 6, brez test)", summary.valid_rows_status6_no_test],
  ["Veljavni odgovori z razreseno kodo", summary.valid_rows_with_resolved_code],
  ["Unikatni udelezenci", summary.unique_participants_resolved],
  ["Nerazreseni veljavni vnosi", summary.unresolved_valid_rows.length],
];
addTable(summarySheet, 4, 1, metricRows);

const resolutionRows = [["Razresitev kod", "St. vrstic"]];
for (const [key, value] of Object.entries(summary.resolution_counts)) {
  resolutionRows.push([key, value]);
}
summarySheet.getRange("D3").values = [["Razresitev kod med veljavnimi"]];
summarySheet.getRange("D3").format.font = { name: "Calibri", size: 12, bold: true, color: "#16324F" };
addTable(summarySheet, 4, 4, resolutionRows);

const participationRows = [["St. sodelovanj", "St. udelezencev"]];
for (const [key, value] of Object.entries(summary.participation_distribution)) {
  participationRows.push([key, value]);
}
summarySheet.getRange("A12").values = [["Porazdelitev sodelovanj"]];
summarySheet.getRange("A12").format.font = { name: "Calibri", size: 12, bold: true, color: "#16324F" };
addTable(summarySheet, 13, 1, participationRows);

summarySheet.charts.add("bar", {
  title: "Stevilo udelezencev po stevilu sodelovanj",
  titleTextStyle: { fontSize: 13, bold: true },
  categories: participationRows.slice(1).map((row) => `x${row[0]}`),
  series: [{ name: "Udelezenci", values: participationRows.slice(1).map((row) => row[1]) }],
  hasLegend: false,
  barOptions: { direction: "column", grouping: "clustered", gapWidth: 55 },
  dataLabels: { showValue: true },
  from: { row: 2, col: 6 },
  extent: { widthPx: 470, heightPx: 280 },
});

summarySheet.getRange("A:J").format.autofitColumns();

const participantSheet = workbook.worksheets.add("Udelezenci");
participantSheet.getRange("A1").values = [["Sodelovanja po posamezni kodi"]];
participantSheet.getRange("A1").format.font = { name: "Calibri", size: 14, bold: true, color: "#16324F" };
addTable(participantSheet, 3, 1, makeMatrixFromObjects(participantSummary), true);
participantSheet.freezePanes.freezeRows(3);
participantSheet.freezePanes.freezeColumns(1);
participantSheet.getRange("A:N").format.autofitColumns();

const weekSheet = workbook.worksheets.add("Po tednih");
weekSheet.getRange("A1").values = [["Matrika sodelovanj po kodah in tednih"]];
weekSheet.getRange("A1").format.font = { name: "Calibri", size: 14, bold: true, color: "#16324F" };
addTable(weekSheet, 3, 1, makeMatrixFromObjects(participantWeekMatrix));
weekSheet.freezePanes.freezeRows(3);
weekSheet.freezePanes.freezeColumns(1);
weekSheet.getRange("A:H").format.autofitColumns();

const outputPath = path.join(baseDir, "anketa191776-2026-05-11_analiza_v2.xlsx");
const output = await SpreadsheetFile.exportXlsx(workbook);
await output.save(outputPath);

console.log(outputPath);
