/*
  Global variables
*/

// const { dialog } = require('electron');
// let remote = require('electron').remote; 
// let dialog = remote.dialog;

 let data = [
[
    "TMT1",
    "wt 1",
    "0.01",
    15,
    5
],
[
    "TMT1",
    "wt 2",
    "0.01",
    15,
    5
],
[
    "TMT1",
    "wt 3",
    "0.01",
    15,
    5
],
[
    "TMT2",
    "wt 1",
    "0.01",
    15,
    5
],
[
    "TMT2",
    "wt 2",
    "0.01",
    15,
    5
],
[
    "TMT2",
    "wt 3",
    "0.01",
    15,
    5
],
[
    "TMT2",
    "wt 4",
    "0.01",
    15,
    5
]
];
let header = ["experiment", "name", "FDR", "Tolerance", "Jumps"];

let container = $('#hot_pratio_tasktbl').handsontable({
data: data,
colHeaders: header,
minRows: 1,
minCols: 2,
minSpareRows: 1,
rowHeaders: true,
contextMenu: true,
manualColumnResize: true,
// formulas: true,
// manualRowMove: true,
// manualColumnMove: true,
// filters: true,
// dropdownMenu: true,
// mergeCells: true,
// columnSorting: true,
// sortIndicator: true,
// autoColumnSize: {
//     samplingRatio: 23
// }
// fixedRowsTop: 2,
// fixedColumnsLeft: 3        
});


