/*
 * Handle parameters
 */
let remote = require('electron').remote;
var path = require('path');
let dialog = remote.dialog;
let fs = require('fs');
let dtablefilename = 'isanxot_dta.csv';
let cfgfilename = 'isanxot_cfg.json'

/*
* Export tasktable to CSV
*/
function parseRow(sizeData, index, infoArray) {
    let cont = "";
    if (index < sizeData - 1) {
        dataString = "";
            infoArray.forEach(function(col,i) {            
            dataString += _.contains(col, ",") ? "\"" + col + "\"" : col;
            dataString += i < _.size(infoArray) - 1 ? "," : "";
        })
        cont = index < sizeData - 2 ? dataString + "\n" : dataString;
    }
    return cont;
}
function exporttasktableCSV(tasktable) {
    // add header
    let csvContent = tasktable.getColHeader().join(",") + "\n";
    let data = tasktable.getData();
    let sizeData = data.length;
    data.forEach(function(row,idx) {
        csvContent += parseRow(sizeData, idx, row);
    });
    return csvContent;
}

// Create tasktable file
function createtasktableFile(outdir) {
    // export tasktable to CSV
    try {
        let tasktable = $("#hot").data('handsontable');
        var cont = exporttasktableCSV(tasktable);
    } catch (err) {
        console.log(`Error exporting tasktable: ${err}`);
        return false;
    }
    // write file sync
    let file = outdir +'/'+ dtablefilename;
    try {
        fs.writeFileSync(file, cont, 'utf-8');
    } catch (err) {    
        console.log(`Error writing tasktable file: ${err}`);
        return false;
    }
    return file;
}


/*
* Global functions
*/
function getInFileDir(tid) {
    let f = document.querySelector('#'+tid).value;
    try {
        if (!fs.existsSync(f)){
            console.log(`given ${tid} does not exist: ${f}`);
            return false;
        }
    } catch (err) {    
        console.log(`Error getting ${tid}: ${err}`);
        return false;
    }
    f = f.replace(/\\/g, "/");
    return f;
} // end getInFileDir

function createLocalDir(tid) {
    let f = document.querySelector('#'+tid).value;
    try {
        if (!fs.existsSync(f)){
            fs.mkdirSync(f);
        }
    } catch (err) {    
        console.log(`Error creating local ${tid}: ${err}`);
        return false;
    }    
    f = f.replace(/\\/g, "/");
    return f;
} // end createLocalDir

  
/*
* Create config file 
*/
// traverse all the Nodes of a JSON Object Tree
// function traverse(jsonObj, jsonKey="") {
//     if ( jsonObj !== null && typeof jsonObj == "object" ) {
//         Object.entries(jsonObj).forEach(([key, val]) => {
//             // key is either an array index or object key
//             traverse(val, jsonKey+"/"+key);
//         });
//     } else {
//         jsonObj 
//         // jsonObj is a number or string
//         console.log(`${key} ${jsonObj}` );
//     }
// }
function replaceConsts(data) {

    //convert to JSON string
    let sdta = JSON.stringify(data);
    // var odata = sdta.replace(/--WF__INFILE__NAMES--/g, value);
    // replace constants
    sdta = sdta.replace(/--WF__INDATA--/g, data["indata"]);
    sdta = sdta.replace(/--WF__INDIR--/g, data["indir"]);
    sdta = sdta.replace(/--WF__INFILE__NAMES--/g, data["infilenames"]);
    sdta = sdta.replace(/--WF__INFILE__DB--/g, data["dbfile"]);
    sdta = sdta.replace(/--WF__INFILE__CAT--/g, data["catfile"]);
    sdta = sdta.replace(/--WF__OUTDIR--/g, data["outdir"]);
    sdta = sdta.replace(/--WF__WKS__TMPDIR--/g, data["tmpdir"]);
    sdta = sdta.replace(/--WF__WKS__RSTDIR--/g, data["rstdir"]);
    sdta = sdta.replace(/--WF__WKS__LOGDIR--/g, data["logdir"]);
    // convert back to array
    let dta = JSON.parse(sdta);

    return dta;
} // end replaceTags

function addConfParams(file, params) {
    // get object from template
    let data = JSON.parse(file);

    // add tabledata file
    if ('tskfile' in params) { data['indata'] = params['tskfile']; }    
    // add tabledata file
    if ( 'infile' in params) {
        var dirname  = path.dirname(params['infile']);
        var filename = path.basename(params['infile']);
        data['indir'] = dirname;
        data['infilenames'] = filename;
    }    
    // add tabledata file
    if ('outdir' in params) {
        data['outdir'] = params['outdir'];
        data['tmpdir'] = params['outdir']+'/temp';
        data['rstdir'] = params['outdir']+'/results';
        data['logdir'] = params['outdir']+'/logs';
    }
    // add category
    if ('catfile' in params) { data['catfile'] = params['catfile']; }
    // add db file
    if ('dbfile' in params) { data['dbfile'] = params['dbfile']; }
    // replace tags in the config data
    data = replaceConsts(data)

    return data;
} // end addConfParams

function createConfFile(conf, params) {
    // read template file
    try {
        //file exists, get the contents
        let d = fs.readFileSync(conf);
        // create config data with the parameters
        let data = addConfParams(d, params);
        // convert JSON to string
        var cont = JSON.stringify(data, undefined, 2);
    } catch (err) {
        console.log(`Error creating config file: ${err}`);
        return false;
    }
    // write file sync
    let file = params['outdir'] +'/'+ cfgfilename;
    try {
        fs.writeFileSync(file, cont, 'utf-8');
    } catch (err) {    
        console.log(`Error writing config file: ${err}`);
        return false;
    }
    return file;
} // end createLblConfFile


/*
 * Create parameters to workflow
 */
function createAdvParameters(conf) {
    let params = {};

    // get input directory
    let indir = getInFileDir('indir');
    if ( !indir ) {
        exceptor.showMessageBox('Error Message', 'Input directory is required');
        return false;
    }
    else { params.indir = indir }
    // get and create check and get: output directory
    let outdir = createLocalDir('outdir');
    if ( !outdir ) {
        exceptor.showMessageBox('Error Message', 'Output directory is required');
        return false;
    }
    else { params.outdir = outdir }
    // create tasktable file
    let dtablefile = createtasktableFile(outdir); 
    if ( !dtablefile ) {
        exceptor.showMessageBox('Error Message', 'Creating tasktable file');
        return false;
    }
    // create category file
    let catfile = getInFileDir('catfile');
    if ( !catfile ) {
        exceptor.showMessageBox('Error Message', 'Category file is required');
        return false;
    }
    // Create Config file
    let cfgfile = createConfFile(conf, {
        'indir': indir,
        'outdir': outdir,
        'tskfile': dtablefile,
        'catfile': catfile
    });
    if ( !cfgfile ) {
        exceptor.showMessageBox('Error Message', 'Creating config file');
        return false;
    }
    else { params.cfgfile = cfgfile }
    // get: num threads
    params.nthreads = document.querySelector('#nthreads').value;

    return params;
}
function createLblFreeParameters(conf) {
    let params = {};

    // get input file
    let infile = getInFileDir('infile');
    if ( !infile ) {
        exceptor.showMessageBox('Error Message', 'Input file is required');
        return false;
    }
    else { params.infile = infile }
    // get and create check and get: output directory
    let outdir = createLocalDir('outdir');
    if ( !outdir ) {
        exceptor.showMessageBox('Error Message', 'Output directory is required');
        return false;
    }
    else { params.outdir = outdir }
    // create tasktable file
    let dtablefile = createtasktableFile(outdir); 
    if ( !dtablefile ) {
        exceptor.showMessageBox('Error Message', 'Creating tasktable file');
        return false;
    }
    // create db file
    let dbfile = getInFileDir('dbfile');
    if ( !dbfile ) {
        exceptor.showMessageBox('Error Message', 'Database file is required');
        return false;
    }
    // create category file
    let catfile = getInFileDir('catfile');
    if ( !catfile ) {
        exceptor.showMessageBox('Error Message', 'Category file is required');
        return false;
    }
    // Create Config file
    let cfgfile = createConfFile(conf, {
        'infile': infile,
        'outdir': outdir,
        'tskfile': dtablefile,
        'catfile': catfile,
        'dbfile': dbfile
    });
    if ( !cfgfile ) {
        exceptor.showMessageBox('Error Message', 'Creating config file');
        return false;
    }
    else { params.cfgfile = cfgfile }
    // get: num threads
    params.nthreads = document.querySelector('#nthreads').value;

    return params;
}
function createParameters(conf) {
    let params = false;
    if ( conf.search(/simple/) != -1 ) {
        params = createSmpParameters(conf);
    } else if ( conf.search(/advance/) != -1 ) {
        params = createAdvParameters(conf);
    } else if ( conf.search(/labelfree/) != -1 ) {
        params = createLblFreeParameters(conf);
    } else {
        params = false;
    }
    return params;
}

// We assign properties to the `module.exports` property, or reassign `module.exports` it to something totally different.
// In  the end of the day, calls to `require` returns exactly what `module.exports` is set to.
module.exports.createParameters = createParameters;



/*
 * Events
 */

// for Database
if ( document.getElementById('select-indir') !== null ) {
    document.getElementById('select-indir').addEventListener('click', function(){
        dialog.showOpenDialog({ properties: ['openDirectory']}, function (dirs) {
            if(dirs === undefined){
                console.log("No input directory selected");
            } else{
                document.getElementById("indir").value = dirs[0];
            }
        }); 
    },false);    
}
if ( document.getElementById('select-infile') !== null ) {
    document.getElementById('select-infile').addEventListener('click', function(){
        dialog.showOpenDialog({ properties: ['openFile']}, function (files) {
            if( files === undefined ){
                console.log("No input file selected");
            } else{
                document.getElementById("infile").value = files[0];
            }
        });
    });
}
if ( document.getElementById('select-outdir') !== null ) {
    document.getElementById('select-outdir').addEventListener('click', function(){
        dialog.showOpenDialog({ properties: ['openDirectory']}, function (dirs) {
            if(dirs === undefined){
                console.log("No output directory selected");
            } else{
                document.getElementById("outdir").value = dirs[0];
            }
        }); 
    },false);
}

if ( document.getElementById('def-catfile') !== null ) {
    document.getElementById('def-catfile').addEventListener('change', function(){
        if ( this.value === "personal" ) {
            document.getElementById('catfile').value = "";
            document.getElementById("catfile").disabled = false;
            document.getElementById("select-catfile").disabled = false;
        }
        else {
            let dbsdir = process.env.ISANXOT_SRC_HOME + '/dbs';
            let files = fs.readdirSync(dbsdir).filter(fn => fn.startsWith(this.value) & fn.endsWith('.tsv'));
            document.getElementById('catfile').value = dbsdir + '/' + files[0];    
            document.getElementById("catfile").disabled = true;
            document.getElementById("select-catfile").disabled = true;
        }
    });
}

if ( document.getElementById('select-catfile') !== null ) {
    document.getElementById('select-catfile').addEventListener('click', function(){
        dialog.showOpenDialog({ properties: ['openFile']}, function (files) {
            if( files === undefined ){
                console.log("No category file selected");
            } else{
                document.getElementById("catfile").value = files[0];
            }
        });
    });
}

/* ---------------- Specific: Simple Mode ------------------ */

// for pRatio
if ( document.getElementById('def-modfile') !== null ) {
    document.getElementById('def-modfile').addEventListener('click', function(){
        if(this.checked) {
            document.getElementById("modfile").disabled = true;
            document.getElementById("select-modfile").disabled = true;
        }
        else {
            document.getElementById("modfile").disabled = false;
            document.getElementById("select-modfile").disabled = false;
        }
    },false);    
}

if ( document.getElementById('select-modfile') !== null ) {
    document.getElementById('select-modfile').addEventListener('click', function(){
        dialog.showOpenDialog({ properties: ['openFile']}, function (files) {
            if( files === undefined ){
                console.log("No modification file selected");
            } else{
                document.getElementById("modfile").value = files[0];
            }
        }); 
    },false);
}

// for SanXot
// if ( document.getElementById('select-catfile') !== null ) {
//     document.getElementById('select-catfile').addEventListener('click', function(){
//         dialog.showOpenDialog({ properties: ['openFile']}, function (files) {
//             if(files === undefined){
//                 console.log("No category file selected");
//             } else{
//                 document.getElementById("catfile").value = files[0];
//             }
//         }); 
//     },false);
// }

// if ( document.getElementById('sample') !== null ) {
//     document.getElementById('sample').addEventListener('click', function(){    
//         if(this.checked) {
//             // <!-- test 1 -->
//             document.getElementById('indir').value = "S:\\LAB_JVC\\RESULTADOS\\JM RC\\iq-Proteo\\PESA_omicas\\3a_Cohorte_120_V2\\TMT_Fraccionamiento";
//             document.getElementById('outdir').value = "S:\\LAB_JVC\\RESULTADOS\\JM RC\\iq-Proteo\\PESA_3a_Cohorte_120_V2_TMTfrac_WF";
//             tasktable.container.handsontable('loadData', tasktable.dtatest);
//             document.getElementById("sample2").checked = false;
//             document.getElementById("sample3").checked = false;
//         } else {
//             // Checkbox is not checked..
//             document.getElementById('indir').value = "";
//             document.getElementById('outdir').value = "";
//             tasktable.container.handsontable('loadData', [[]]);
//             tasktable.container.handsontable('deselectCell');
//             document.getElementById("sample2").checked = true;
//             document.getElementById("sample3").checked = true;
//         }
//     },false);
// }
// if ( document.getElementById('sample2') !== null ) {
//     document.getElementById('sample2').addEventListener('click', function(){    
//         if(this.checked) {
//             // <!-- test 2 -->
//             document.getElementById('indir').value = "S:\\LAB_JVC\\RESULTADOS\\JM RC\\iq-Proteo\\Calsequestrin_null_mice_Sept_17___LC-MS_1st_round";
//             document.getElementById('outdir').value = "S:\\LAB_JVC\\RESULTADOS\\JM RC\\iq-Proteo\\Calseq_WF";
//             tasktable.container.handsontable('loadData', tasktable.dtatest2);
//             document.getElementById("sample").checked = false;
//             document.getElementById("sample3").checked = false;
//         } else {
//             // Checkbox is not checked..
//             document.getElementById('indir').value = "";
//             document.getElementById('outdir').value = "";
//             tasktable.container.handsontable('loadData', [[]]);
//             tasktable.container.handsontable('deselectCell');
//             document.getElementById("sample").checked = true;
//             document.getElementById("sample3").checked = true;
//         }
//     },false);
// }
// if ( document.getElementById('sample3') !== null ) {
//     document.getElementById('sample3').addEventListener('click', function(){    
//         if(this.checked) {
//             // <!-- test 1 -->
//             document.getElementById('indir').value = "S:\\LAB_JVC\\RESULTADOS\\JM RC\\iq-Proteo\\PESA_omicas\\3a_Cohorte_120_V2\\Busqueda_PD";
//             document.getElementById('outdir').value = "S:\\LAB_JVC\\RESULTADOS\\JM RC\\iq-Proteo\\PESA_3a_Cohorte_120_V2_TMTfrac_WF_psm_input";
//             tasktable.container.handsontable('loadData', tasktable.dtatest3);
//             document.getElementById("sample").checked = false;
//             document.getElementById("sample2").checked = false;
//         } else {
//             // Checkbox is not checked..
//             document.getElementById('indir').value = "";
//             document.getElementById('outdir').value = "";
//             tasktable.container.handsontable('loadData', [[]]);
//             tasktable.container.handsontable('deselectCell');
//             document.getElementById("sample").checked = true;
//             document.getElementById("sample2").checked = true;
//         }
//     },false);
// }

// function addSmpConfParams(file, params) {
//     // get object from template
//     let data = JSON.parse(file);

//     // add tabledata file
//     data['indata'] = params['tskfile'];
//     // add tabledata file
//     data['indir'] = params['indir'];
//     // add tabledata file
//     data['outdir'] = params['outdir'];
//     // add modification
//     data['modfile'] = params['modfile'];
//     // add category
//     data['catfile'] = params['catfile'];

//     // wf parameters
//     let wf = data['workflow'];
//     let wf_presanxot2 = wf['presanxot2'];
//     let wf_sanxot = wf['sanxot'];

//     /* --- pRatio --- */
//     wf_presanxot2['pratio']['threshold'] = parseInt(document.querySelector('#deltaMassThreshold').value);
//     wf_presanxot2['pratio']['delta_mass'] = parseInt(document.querySelector('#deltaMassAreas').value);
//     wf_presanxot2['pratio']['tag_mass'] = parseFloat(document.querySelector('#tagMass').value);
//     wf_presanxot2['pratio']['lab_decoy'] = document.querySelector('#tagDecoy').value;


//     /* --- Pre-SanXoT2 --- */
//     // add to presanxot2 the option of included tags
//     // let includeTags = document.querySelector('#includeTags').checked;
//     // if ( includeTags ) {
//     //     // relationship table s2p
//     //     wf_presanxot2['rels2sp']['optparams']['aljamia1'] += ' -l [Tags] ';
//     //     wf_presanxot2['rels2sp']['optparams']['aljamia2'] += ' -k [Tags] ';
//     //     // relationship table p2q
//     //     wf_presanxot2['rels2pq']['optparams']['aljamia1'] += ' -k [Tags] ';
//     //     // relationship table p2q_unique
//     //     wf_presanxot2['rels2pq_unique']['optparams']['aljamia1'] += ' --c5 [Tags] ';        
//     // }

//     /* --- SanXoT --- */
//     // add FDR
//     wf_sanxot['scan2peptide']['fdr'] = parseFloat(document.querySelector('.scan2peptide #fdr').value);
//     wf_sanxot['peptide2protein']['fdr'] = parseFloat(document.querySelector('.peptide2protein #fdr').value);
//     wf_sanxot['protein2category']['fdr'] = parseFloat(document.querySelector('.protein2category #fdr').value);
//     // force the variance if apply
//     if ( !document.querySelector('.scan2peptide #variance').disabled ) {
//         wf_sanxot['scan2peptide']['variance'] = parseFloat(document.querySelector('.scan2peptide #variance').value);
//     }
//     if ( !document.querySelector('.peptide2protein #variance').disabled ) {
//         wf_sanxot['peptide2protein']['variance'] = parseFloat(document.querySelector('.peptide2protein #variance').value);
//     }
//     if ( !document.querySelector('.protein2category #variance').disabled ) {
//         wf_sanxot['protein2category']['variance'] = parseFloat(document.querySelector('.protein2category #variance').value);
//     }    
//     // Discard outliers
//     let discardOutliers = document.querySelector('#discardOutliers').checked;
//     if ( discardOutliers ) {
//         wf_sanxot['scan2peptide']['optparams']['sanxot2'] += ' --tags !out ';
//         wf_sanxot['peptide2protein']['optparams']['sanxot2'] += ' --tags !out ';
//         wf_sanxot['protein2category']['optparams']['sanxot2'] += ' --tags !out ';
//     }

//     return data;

// } // end addSmpConfParams


// function addAdvConfParams(file, params) {
//     // get object from template
//     let data = JSON.parse(file);

//     // add tabledata file
//     data['indata'] = params['tskfile'];
//     // add tabledata file
//     data['indir'] = params['indir'];
//     // add tabledata file
//     data['outdir'] = params['outdir'];
//     // add category
//     data['catfile'] = params['catfile'];

//     // wf parameters
//     let wf = data['workflow'];
//     let wf_sanxot = wf['sanxot'];

//     /* --- SanXoT --- */
//     // Discard outliers
//     let discardOutliers = document.querySelector('#discardOutliers').checked;
//     if ( discardOutliers ) {
//         wf_sanxot['scan2peptide']['optparams']['sanxot2'] += ' --tags !out ';
//         wf_sanxot['peptide2protein']['optparams']['sanxot2'] += ' --tags !out ';
//         wf_sanxot['protein2category']['optparams']['sanxot2'] += ' --tags !out ';
//     }

//     return data;
// } // end addAdvConfParams

