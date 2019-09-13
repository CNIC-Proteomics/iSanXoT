/*
  Global variables
*/

let header = ["experiment", "name", "ratio_numerator", "ratio_denominator", "s>p FDR", "p>q FDR", "q>c FDR","s>p Var(x)", "p>q Var(x)", "q>c Var(x)"];

let container = $('#hot').handsontable({
  data: [[]],
  colWidths: 100,
  width: '100%',
  height: 320,
  rowHeights: 23,
  rowHeaders: true,
  colHeaders: header,
  minRows: 2,
  minCols: header.length,
  minSpareRows: 1,
  contextMenu: true,
  manualColumnResize: true,
  licenseKey: 'non-commercial-and-evaluation'
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