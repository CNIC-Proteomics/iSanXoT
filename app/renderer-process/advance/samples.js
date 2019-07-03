/* Data samples */

let dtatest = [
  ["TMT1","wt 1","126","126,131",0.01,0.01,0.01,false,false,false],
  ["TMT1","wt 2","127_N","126,131",0.01,0.01,0.01,false,false,false],
  ["TMT1","wt 3","127_C","126,131",0.01,0.01,0.01,false,false,false],
  ["TMT1","wt 4","128_N","126,131",0.01,0.01,0.01,false,false,false],
  ["TMT1","KO 1","128_C","126,131",0.01,0.01,0.01,false,false,false],
  ["TMT1","KO 2","129_N","126,131",0.01,0.01,0.01,false,false,false],
  ["TMT1","KO3","129_C","126,131",0.01,0.01,0.01,false,false,false],
  ["TMT1","KO4","130_N","126,131",0.01,0.01,0.01,false,false,false],
  ["TMT1","h34571","130_C","126,131",0.01,0.01,0.01,false,false,false],
  ["TMT1","h34572","131","126,131",0.01,0.01,0.01,false,false,false],
  ["TMT2","wt 1","126","126,131",0.01,0.01,0.01,false,false,false],
  ["TMT2","wt 2","127_N","126,131",0.01,0.01,0.01,false,false,false],
  ["TMT2","wt 3","127_C","126,131",0.01,0.01,0.01,false,false,false],
  ["TMT2","wt 4","128_N","126,131",0.01,0.01,0.01,false,false,false],
  ["TMT2","KO 1","128_C","126,131",0.01,0.01,0.01,false,false,false],
  ["TMT2","KO 2","129_N","126,131",0.01,0.01,0.01,false,false,false],
  ["TMT2","KO3","129_C","126,131",0.01,0.01,0.01,false,false,false],
  ["TMT2","KO4","130_N","126,131",0.01,0.01,0.01,false,false,false],
  ["TMT2","h34571","130_C","126,131",0.01,0.01,0.01,false,false,false],
  ["TMT2","h34572","131","126,131",0.01,0.01,0.01,false,false,false]
];
  
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

/* Events */

if ( document.getElementById('sample') != null ) {
  document.getElementById('sample').addEventListener('click', function(){
      if(this.checked) {
          // <!-- test 1 -->
          document.getElementById('indir').value = process.env.ISANXOT_SRC_HOME + "\\tests\\PESA omicas\\3a_Cohorte_120_V2\\TMT_Fraccionamiento";
          document.getElementById('outdir').value = process.env.ISANXOT_SRC_HOME + "\\tests\\PESA omicas\\wf_results_PESA_3a_Cohorte_120_V2_TMTfrac";
          document.getElementById('def-catfile').value = 'human';
          document.getElementById('catfile').value = process.env.ISANXOT_SRC_HOME + '\\dbs\\human_UP000005640_201904.tsv';
          tasktable.container.handsontable('loadData', dtatest);
          document.getElementById("sample2").checked = false;
          document.getElementById("sample3").checked = false;
      } else {
          // Checkbox is not checked..
          document.getElementById('indir').value = "";
          document.getElementById('outdir').value = "";
          tasktable.container.handsontable('loadData', [[]]);
          tasktable.container.handsontable('deselectCell');
          document.getElementById("sample2").checked = true;
          document.getElementById("sample3").checked = true;
      }
  },false);
}
if ( document.getElementById('sample2') != null ) {
  document.getElementById('sample2').addEventListener('click', function(){    
      if(this.checked) {
          // <!-- test 2 -->
          document.getElementById('indir').value = "S:\\LAB_JVC\\RESULTADOS\\JM RC\\iq-Proteo\\Calsequestrin_null_mice_Sept_17___LC-MS_1st_round";
          document.getElementById('outdir').value = "S:\\LAB_JVC\\RESULTADOS\\JM RC\\iq-Proteo\\Calseq_WF";
          tasktable.container.handsontable('loadData', dtatest2);
          document.getElementById("sample").checked = false;
          document.getElementById("sample3").checked = false;
      } else {
          // Checkbox is not checked..
          document.getElementById('indir').value = "";
          document.getElementById('outdir').value = "";
          tasktable.container.handsontable('loadData', [[]]);
          tasktable.container.handsontable('deselectCell');
          document.getElementById("sample").checked = true;
          document.getElementById("sample3").checked = true;
      }
  },false);
}
if ( document.getElementById('sample3') != null ) {
  document.getElementById('sample3').addEventListener('click', function(){    
      if(this.checked) {
          // <!-- test 1 -->
          document.getElementById('indir').value = "S:\\LAB_JVC\\RESULTADOS\\JM RC\\iq-Proteo\\PESA_omicas\\3a_Cohorte_120_V2\\Busqueda_PD";
          document.getElementById('outdir').value = "S:\\LAB_JVC\\RESULTADOS\\JM RC\\iq-Proteo\\PESA_3a_Cohorte_120_V2_TMTfrac_WF_psm_input";
          tasktable.container.handsontable('loadData', dtatest3);
          document.getElementById("sample").checked = false;
          document.getElementById("sample2").checked = false;
      } else {
          // Checkbox is not checked..
          document.getElementById('indir').value = "";
          document.getElementById('outdir').value = "";
          tasktable.container.handsontable('loadData', [[]]);
          tasktable.container.handsontable('deselectCell');
          document.getElementById("sample").checked = true;
          document.getElementById("sample2").checked = true;
      }
  },false);
}
