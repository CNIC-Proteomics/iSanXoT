/*
 * Handle parameters
 */
let remote = require('electron').remote;
let path = require('path');
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
//         // jsonObj is a number or string
//         console.log(`${key} ${jsonObj}` );
//     }
// }
// function traverse(jsonObj, jsonKey="", method=null) {
function addParamsInMethod(jsonObj, method=null, params) {
    Object.entries(jsonObj).forEach(([key, val]) => {
        Object.entries(val["methods"]).forEach(([k, v]) => {
            if ( v["script"] == method) {
                for ( let i in params ) {
                    let param = params[i];
                    v["params"][param.attr] = param.val;
                }
            }
        });
    });
} // end addParamInMethod

function addParams(data) {
    // create var with the parameter values    
    let params = []
    if (document.querySelector('#deltaMassThreshold')) { // pRatio
        let val = document.querySelector('#deltaMassThreshold').value;
        params.push({ "attr": "--threshold", "val": val });        
    }
    if (document.querySelector('#deltaMassAreas')) { // pRatio
        let val = document.querySelector('#deltaMassAreas').value;
        params.push({ "attr": "--jump_areas", "val": val });        
    }
    if (document.querySelector('#tagDecoy')) { // pRatio
        let val = document.querySelector('#tagDecoy').value;
        params.push({ "attr": "--lab_decoy", "val": val });        
    }
    // add into config
    if ( params.length !== 0 ) {
        addParamsInMethod(data["workflow"]["rules"], "preSanXoT/fdr.py", params )
    }
    
    return data
} // end addParams

function replaceConsts(data) {
    //convert to JSON string
    let sdta = JSON.stringify(data);
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
    if ('indir'   in params) { data['indir'] = params['indir']; }
    // add tabledata file
    if ('infile'  in params) {
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
    // add parameters
    data = addParams(data)    
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
