/*
  Global variables
*/

let header = ["experiment", "name", "ratio_numerator", "ratio_denominator", "s>p FDR", "p>q FDR", "q>c FDR","s>p Var(x)", "p>q Var(x)", "q>c Var(x)"];

// nestedHeaders: [
//   ['A', {label: 'B', colspan: 8}, 'C'],
//   ['D', {label: 'E', colspan: 4}, {label: 'F', colspan: 4}, 'G'],
//   ['H', {label: 'I', colspan: 2}, {label: 'J', colspan: 2}, {label: 'K', colspan: 2}, {label: 'L', colspan: 2}, 'M'],
//   ['N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W']
// ]

// let hot = document.getElementById('hot');
// let container = new Handsontable(hot, {
let container = $('#hot').handsontable({  
data: [[]],
colHeaders: header,
// colHeaders: true,
// nestedHeaders: header,
minRows: 2,
minCols: header.length,
minSpareRows: 1,
rowHeaders: true,
contextMenu: true,
manualColumnResize: true,
// formulas: false,
// manualRowMove: false,
// manualColumnMove: false,
// filters: false,
// dropdownMenu: false,
// mergeCells: false,
// columnSorting: false,
// sortIndicator: false,
// autoColumnSize: {
//     samplingRatio: 23
// },
// fixedRowsTop: 2,
// fixedColumnsLeft: 3
});

$('a[id="tasktable-tab"]').on('shown.bs.tab', function (e) {
  $('#hot').handsontable('render');
});

let smkfile = process.env.ISANXOT_SRC_HOME + '/wfs/wf_sanxot.smk';
// let cfgfile = process.env.ISANXOT_SRC_HOME + '/wfs/cfg/cfg_labelfree.json';
let cfgfile = process.env.ISANXOT_SRC_HOME + '/wfs/cfg/cfg_labelfree_NOT_GENERAL.json';

// We assign properties to the `module.exports` property, or reassign `module.exports` it to something totally different.
// In  the end of the day, calls to `require` returns exactly what `module.exports` is set to.
module.exports.smkfile = smkfile;
module.exports.cfgfile = cfgfile;
module.exports.container = container;