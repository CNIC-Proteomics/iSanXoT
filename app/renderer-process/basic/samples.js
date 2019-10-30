let tt = require('./tasktable');

/* Data samples */

let dtatest = [
  ["TMT1","wt 1","126","126,131",0.01,0.01,0.01,false,false,false],
  ["TMT1","wt 2","127N","126,131",0.01,0.01,0.01,false,false,false],
  ["TMT1","wt 3","127C","126,131",0.01,0.01,0.01,false,false,false],
  ["TMT1","wt 4","128N","126,131",0.01,0.01,0.01,false,false,false],
  ["TMT1","KO 1","128C","126,131",0.01,0.01,0.01,false,false,false],
  ["TMT1","KO 2","129N","126,131",0.01,0.01,0.01,false,false,false],
  ["TMT1","KO3","129C","126,131",0.01,0.01,0.01,false,false,false],
  ["TMT1","KO4","130N","126,131",0.01,0.01,0.01,false,false,false],
  ["TMT1","h34571","130C","126,131",0.01,0.01,0.01,false,false,false],
  ["TMT1","h34572","131","126,131",0.01,0.01,0.01,false,false,false],
  ["TMT2","wt 1","126","126,131",0.01,0.01,0.01,false,false,false],
  ["TMT2","wt 2","127N","126,131",0.01,0.01,0.01,false,false,false],
  ["TMT2","wt 3","127C","126,131",0.01,0.01,0.01,false,false,false],
  ["TMT2","wt 4","128N","126,131",0.01,0.01,0.01,false,false,false],
  ["TMT2","KO 1","128C","126,131",0.01,0.01,0.01,false,false,false],
  ["TMT2","KO 2","129N","126,131",0.01,0.01,0.01,false,false,false],
  ["TMT2","KO3","129C","126,131",0.01,0.01,0.01,false,false,false],
  ["TMT2","KO4","130N","126,131",0.01,0.01,0.01,false,false,false],
  ["TMT2","h34571","130C","126,131",0.01,0.01,0.01,false,false,false],
  ["TMT2","h34572","131","126,131",0.01,0.01,0.01,false,false,false]
];
// let dtatest = [
//   ["TMT1","wt 1","126","126,131",0.01,0.01,0.01,false,false,false],
//   ["TMT1","wt 2","127N","126,131",0.01,0.01,0.01,false,false,false],
//   ["TMT1","wt 3","127C","126,131",0.01,0.01,0.01,false,false,false],
// ];
  
let dtatest2 = [
  ["Calseq2","wt 1","126","126,131",0.01,0.01,0.01,false,false,false],
  ["Calseq2","wt 2","127_N","126,131",0.01,0.01,0.01,false,false,false],
  ["Calseq","wt 3","127_C","126,131",0.01,0.01,0.01,false,false,false],
  ["Calseq","wt 4","128_N","126,131",0.01,0.01,0.01,false,false,false],
  ["Calseq","wt 5","128_C","126,131",0.01,0.01,0.01,false,false,false],
  ["Calseq","KO 1","129_N","126,131",0.01,0.01,0.01,false,false,false],
  ["Calseq","KO 2","129_C","126,131",0.01,0.01,0.01,false,false,false],
  ["Calseq","KO 3","130_N","126,131",0.01,0.01,0.01,false,false,false],
  ["Calseq","KO 4","130_C","126,131",0.01,0.01,0.01,false,false,false],
  ["Calseq","KO 5","131","126,131",0.01,0.01,0.01,false,false,false]
];
let dtatest3 = [
  ["TMT1"],
  ["TMT2"]
];


/* Events */

if ( document.getElementById('sample') !== null ) {
  document.getElementById('sample').addEventListener('click', function(){
    document.getElementById('indir').value = process.env.ISANXOT_SRC_HOME + "\\tests\\PESA omicas\\3a_Cohorte_120_V2\\Busqueda_PD";
    document.getElementById('outdir').value = process.env.ISANXOT_SRC_HOME + "\\tests\\PESA omicas\\3a_Cohorte_120_V2_wf_results";
    document.getElementById('def-catfile').value = 'personal';
    document.getElementById('catfile').value = process.env.ISANXOT_SRC_HOME + '\\tests\\PESA omicas\\3a_Cohorte_120_V2\\q2cIPA-DAVID-CORUM-Manual-Human3_nd_IPA_PESA_panels.txt';
    document.getElementById('def-dbfile').value = 'personal';
    document.getElementById('dbfile').value = process.env.ISANXOT_SRC_HOME + "\\tests\\PESA omicas\\3a_Cohorte_120_V2\\Human_jul14.fasta";
    document.getElementById('experiments').value = "TMT1,TMT2";
    // tt.container.loadData(dtatest);
    tt.container.handsontable('loadData', dtatest);
    document.getElementById('tagDecoy').value = '_INV_';
    document.querySelector('#nthreads').value = 20;
  },false);
}
// if ( document.getElementById('sample2') !== null ) {
//   document.getElementById('sample2').addEventListener('click', function(){    
//     document.getElementById('indir').value = "S:\\LAB_JVC\\RESULTADOS\\JM RC\\iq-Proteo\\Calsequestrin_null_mice_Sept_17___LC-MS_1st_round";
//     document.getElementById('outdir').value = "S:\\LAB_JVC\\RESULTADOS\\JM RC\\iq-Proteo\\Calseq_WF";
//     // tt.container.loadData(dtatest2);
//     tt.container.handsontable('loadData', dtatest2);
//   },false);  
// }
if ( document.getElementById('sample3') !== null ) {
  function disable_checkbox_method(id) {
    $(`${id}`).prop('disabled', true);
    $(`${id}`).prop('checked', false);
  }
  function discard_parameter(id) {
      $(`div[name="${id}"]`).hide();
      $(`#${id}`).attr("discard",true);
  }

  document.getElementById('sample3').addEventListener('click', function(){    
    document.getElementById('indir').value = "D:\\projects\\iSanXoT\\tests\\PESA omicas\\3a_Cohorte_120_V2\\Busqueda_PD";
    document.getElementById('outdir').value = "D:\\projects\\iSanXoT\\tests\\PESA omicas\\3a_Cohorte_120_V2_wf_results_test_pratio";
    disable_checkbox_method(`#select-methods #ratios`);
    disable_checkbox_method(`#select-methods #sanxot`);
    // $(`a#tasktable-tab`).hide();
    // discard_parameter('hot');
    tt.container.handsontable('loadData', dtatest3);
    discard_parameter('select-catfile');
    discard_parameter('catfile');
    discard_parameter('def-species');
    document.getElementById('experiments').value = "TMT1,TMT2";
    document.getElementById('def-dbfile').value = 'personal';
    document.getElementById('dbfile').value = process.env.ISANXOT_SRC_HOME + "\\tests\\PESA omicas\\3a_Cohorte_120_V2\\Human_jul14.fasta";
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