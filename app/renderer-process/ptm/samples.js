let tt = require('./tasktable');

/* Data samples */

let dtatest = [
  ["TMT1","wt 1","X126","X126",0.01,0.01,0.01,false,false,false],
  ["TMT1","wt 2","X127_N","X126",0.01,0.01,0.01,false,false,false],
  ["TMT1","wt 3","X127_C","X126",0.01,0.01,0.01,false,false,false],
  ["TMT1","wt 4","X128_N","X126",0.01,0.01,0.01,false,false,false],
  ["TMT1","KO 1","X128_C","X126",0.01,0.01,0.01,false,false,false],
  ["TMT1","KO 2","X129_N","X126",0.01,0.01,0.01,false,false,false],
  ["TMT1","KO3","X129_C","X126",0.01,0.01,0.01,false,false,false],
  ["TMT1","KO4","X130_N","X126",0.01,0.01,0.01,false,false,false],
  ["TMT1","h34571","X130_C","X126",0.01,0.01,0.01,false,false,false],
  ["TMT1","h34572","X131","X126",0.01,0.01,0.01,false,false,false],

  ["TMT2","wt 1","X126","X126",0.01,0.01,0.01,false,false,false],
  ["TMT2","wt 2","X127_N","X126",0.01,0.01,0.01,false,false,false],
  ["TMT2","wt 3","X127_C","X126",0.01,0.01,0.01,false,false,false],
  ["TMT2","wt 4","X128_N","X126",0.01,0.01,0.01,false,false,false],
  ["TMT2","KO 1","X128_C","X126",0.01,0.01,0.01,false,false,false],
  ["TMT2","KO 2","X129_N","X126",0.01,0.01,0.01,false,false,false],
  ["TMT2","KO3","X129_C","X126",0.01,0.01,0.01,false,false,false],
  ["TMT2","KO4","X130_N","X126",0.01,0.01,0.01,false,false,false],
  ["TMT2","h34571","X130_C","X126",0.01,0.01,0.01,false,false,false],
  ["TMT2","h34572","X131","X126",0.01,0.01,0.01,false,false,false],

  ["TMT3","wt 1","X126","X126",0.01,0.01,0.01,false,false,false],
  ["TMT3","wt 2","X127_N","X126",0.01,0.01,0.01,false,false,false],
  ["TMT3","wt 3","X127_C","X126",0.01,0.01,0.01,false,false,false],
  ["TMT3","wt 4","X128_N","X126",0.01,0.01,0.01,false,false,false],
  ["TMT3","KO 1","X128_C","X126",0.01,0.01,0.01,false,false,false],
  ["TMT3","KO 2","X129_N","X126",0.01,0.01,0.01,false,false,false],
  ["TMT3","KO3","X129_C","X126",0.01,0.01,0.01,false,false,false],
  ["TMT3","KO4","X130_N","X126",0.01,0.01,0.01,false,false,false],
  ["TMT3","h34571","X130_C","X126",0.01,0.01,0.01,false,false,false],
  ["TMT3","h34572","X131","X126",0.01,0.01,0.01,false,false,false],

  ["TMT4","wt 1","X126","X126",0.01,0.01,0.01,false,false,false],
  ["TMT4","wt 2","X127_N","X126",0.01,0.01,0.01,false,false,false],
  ["TMT4","wt 3","X127_C","X126",0.01,0.01,0.01,false,false,false],
  ["TMT4","wt 4","X128_N","X126",0.01,0.01,0.01,false,false,false],
  ["TMT4","KO 1","X128_C","X126",0.01,0.01,0.01,false,false,false],
  ["TMT4","KO 2","X129_N","X126",0.01,0.01,0.01,false,false,false],
  ["TMT4","KO3","X129_C","X126",0.01,0.01,0.01,false,false,false],
  ["TMT4","KO4","X130_N","X126",0.01,0.01,0.01,false,false,false],
  ["TMT4","h34571","X130_C","X126",0.01,0.01,0.01,false,false,false],
  ["TMT4","h34572","X131","X126",0.01,0.01,0.01,false,false,false],

];


/* Events */

if ( document.getElementById('sample') !== null ) {
  document.getElementById('sample').addEventListener('click', function(){
    document.getElementById('indir').value = process.env.ISANXOT_SRC_HOME + "\\tests\\PTMs\\Edema_Oxidation_timecourse_Cys_pig";
    document.getElementById('outdir').value = process.env.ISANXOT_SRC_HOME + "\\tests\\PTMs\\Edema_Oxidation_timecourse_Cys_pig_results";
    document.getElementById('def-catfile').value = 'human';
    document.getElementById('catfile').value = process.env.ISANXOT_SRC_HOME + '\\dbs\\current_release\\human_UP000005640_sw-tr.cat.tsv';
    tt.container.handsontable('loadData', dtatest);
  },false);
}

if ( document.getElementById('sample-clear') !== null ) {
  document.getElementById('sample-clear').addEventListener('click', function(){    
    document.getElementById('indir').value = "";
    document.getElementById('outdir').value = "";
    document.getElementById('def-catfile').value = 'personal';
    document.getElementById('catfile').value = "";
    tt.container.handsontable('loadData', [[]]);
    tt.container.handsontable('deselectCell');
  },false);
}