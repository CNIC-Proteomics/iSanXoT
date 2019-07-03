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
    "126",
    "",
    "0.01",
    "0.01",
    "0.01",
    false,
    false,
    false
],
[
    "TMT1",
    "wt 2",
    "127_N",
    "126,131",
    "0.01",
    "0.01",
    "0.01",
    false,
    false,
    false
],
[
    "TMT1",
    "wt 3",
    "127_C",
    "126,131",
    "0.01",
    "0.01",
    "0.01",
    false,
    false,
    false
],
[
    "TMT2",
    "wt 1",
    "126",
    "",
    "0.01",
    "0.01",
    "0.01",
    false,
    false,
    false
],
[
    "TMT2",
    "wt 2",
    "127_N",
    "126,131",
    "0.01",
    "0.01",
    "0.01",
    false,
    false,
    false
],
[
    "TMT2",
    "wt 3",
    "127_C",
    "126,131",
    "0.01",
    "0.01",
    "0.01",
    false,
    false,
    false
],
[
    "TMT2",
    "wt 4",
    "128_N",
    "126,131",
    "0.01",
    "0.01",
    "0.01",
    false,
    false,
    false
]
];
let header = ["experiment", "name", "ratio_numerator", "ratio_denominator", "s2p_FDR", "p2q_FDR", "q2c_FDR", "s2p_Var", "p2q_Var", "q2c_Var" ];

let container = $('#hot_sanxot_tasktbl').handsontable({
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


