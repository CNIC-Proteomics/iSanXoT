let tt = require('./tasktable');

/* Data samples */

let dtatest = [
  ["B","b1","B_01","A_01",0.01,0.01,0.01,false,false,false],
  ["B","b2","B_02","A_02",0.01,0.01,0.01,false,false,false],
  ["B","b3","B_03","A_03",0.01,0.01,0.01,false,false,false],
  ["B","b4","B_04","A_04",0.01,0.01,0.01,false,false,false]
];
  

/* Events */

if ( document.getElementById('sample') !== null ) {
  document.getElementById('sample').addEventListener('click', function(){    
    document.getElementById('infile').value = process.env.ISANXOT_SRC_HOME + "\\tests\\label_free\\modificationSpecificPeptides.txt";
    document.getElementById('outdir').value = process.env.ISANXOT_SRC_HOME + "\\tests\\label_free\\wf_results";
    document.getElementById('def-dbfile').value = 'personal';
    document.getElementById('dbfile').value = process.env.ISANXOT_SRC_HOME + "\\tests\\label_free\\HumanSaccEcoliPME12.fasta";
    document.getElementById("dbfile").disabled = false;
    document.getElementById('def-catfile').value = 'human';
    document.getElementById('catfile').value = process.env.ISANXOT_SRC_HOME + "\\dbs\\human_UP000005640_201904.tsv";
    document.getElementById("catfile").disabled = false;
    tt.container.handsontable('loadData', dtatest);
  },false);
// document.getElementById('sample').addEventListener('click', function(){    
  //     if(this.checked) {
  //         // <!-- test 1 -->
  //         document.getElementById('infile').value = process.env.ISANXOT_SRC_HOME + "\\tests\\label_free\\modificationSpecificPeptides.txt";
  //         document.getElementById('outdir').value = process.env.ISANXOT_SRC_HOME + "\\tests\\label_free\\wf_results";
  //         document.getElementById('def-dbfile').value = 'personal';
  //         document.getElementById('dbfile').value = process.env.ISANXOT_SRC_HOME + "\\tests\\label_free\\HumanSaccEcoliPME12.fasta";
  //         document.getElementById("dbfile").disabled = false;
  //         document.getElementById('def-catfile').value = 'human';
  //         document.getElementById('catfile').value = process.env.ISANXOT_SRC_HOME + "\\dbs\\human_UP000005640_201904.tsv";
  //         document.getElementById("catfile").disabled = false;
  //         // tt.container.loadData(dtatest);
  //         tt.container.handsontable('loadData', dtatest);
  //     }
  // },false);
}
if ( document.getElementById('sample-clear') !== null ) {
  document.getElementById('sample-clear').addEventListener('click', function(){    
    document.getElementById('infile').value = "";
    document.getElementById('outdir').value = "";
    document.getElementById('def-dbfile').value = 'personal';
    document.getElementById('dbfile').value = "";
    document.getElementById("dbfile").disabled = false;
    document.getElementById('def-catfile').value = 'personal';
    document.getElementById('catfile').value = "";
    document.getElementById("catfile").disabled = false;
    tt.container.handsontable('loadData', [[]]);
  },false);
// document.getElementById('sample').addEventListener('click', function(){    
  //     if(this.checked) {
  //         // <!-- test 1 -->
  //         document.getElementById('infile').value = process.env.ISANXOT_SRC_HOME + "\\tests\\label_free\\modificationSpecificPeptides.txt";
  //         document.getElementById('outdir').value = process.env.ISANXOT_SRC_HOME + "\\tests\\label_free\\wf_results";
  //         document.getElementById('def-dbfile').value = 'personal';
  //         document.getElementById('dbfile').value = process.env.ISANXOT_SRC_HOME + "\\tests\\label_free\\HumanSaccEcoliPME12.fasta";
  //         document.getElementById("dbfile").disabled = false;
  //         document.getElementById('def-catfile').value = 'human';
  //         document.getElementById('catfile').value = process.env.ISANXOT_SRC_HOME + "\\dbs\\human_UP000005640_201904.tsv";
  //         document.getElementById("catfile").disabled = false;
  //         // tt.container.loadData(dtatest);
  //         tt.container.handsontable('loadData', dtatest);
  //     }
  // },false);
}
