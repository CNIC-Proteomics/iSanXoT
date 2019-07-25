/*
 * Handle parameters
 */
let remote = require('electron').remote;
let path = require('path');
let dialog = remote.dialog;
let fs = require('fs');

let dtablefilename = 'isanxot_dta.csv';
let cfgfilename = 'isanxot_cfg.json';
let logfilename = 'isanxot.log';


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
function addParamsInMethod(jsonObj, rules, methods, params) {
    Object.entries(jsonObj).forEach(([key, val]) => {
        if ( rules.includes(parseInt(key)) ) {
            Object.entries(val["methods"]).forEach(([k, v]) => {
                if ( methods.includes(parseInt(k)) ) {
                    v["params"] += ` ${params} `;
                }
            });    
        }
    });
} // end addParamInMethod

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


function createConfData(conf, params, func_addParams) {
    //file exists, get the contents
    let file = fs.readFileSync(conf);
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
    // replace tags in the config data
    data = replaceConsts(data)

    // add specific workflow parameters
    data = func_addParams(data)

    return data;
} // end addConfParams

function createConfFile(data, outdir) {
    // read template file
    try {
        // convert JSON to string
        var cont = JSON.stringify(data, undefined, 2);
    } catch (err) {
        console.log(`Error creating config file: ${err}`);
        return false;
    }
    // write file sync
    let file = outdir +'/'+ cfgfilename;
    try {
        fs.writeFileSync(file, cont, 'utf-8');
    } catch (err) {    
        console.log(`Error writing config file: ${err}`);
        return false;
    }
    let logfile = outdir +'/'+ logfilename;
    return [file, logfile];
} // end createConfFile


// Export modules
module.exports.createtasktableFile = createtasktableFile;
module.exports.getInFileDir = getInFileDir;
module.exports.createLocalDir = createLocalDir;
module.exports.createConfFile = createConfFile;
module.exports.addParamsInMethod = addParamsInMethod;
module.exports.createConfData = createConfData;
module.exports.createConfFile = createConfFile;



/*
 * Events
 */

$("#select-methods :checkbox").on("change", function(){
    if($(this).is(":checked")){
        // Enable methods
        $("#select-methods :checkbox").prop('disabled', false);
        if( this.id == "fdr" ) {
            // Show tab for the current method
            $('a#params-pratio-tab').show();
        }
        else if( this.id == "pre_sanxot" ) {
            // Show tab for the current method
            $('a#tasktable-tab').show();
        }
        else if( this.id == "sanxot" ) {
            // Show tab for the current method
            $('a#tasktable-tab').show();
        }
    }
    else if($(this).is(":not(:checked)")) {
        // Disable methods depending on which one
        if( this.id == "fdr" ) {
            $("#select-methods :checkbox").prop('disabled', true);
            $(`#select-methods #${this.id}`).prop('disabled', false);
            // Hide tab for the current method and the disabled methods
            $(`a#params-pratio-tab`).hide();
        }
        else if( this.id == "pre_sanxot" ) {
            $("#select-methods :checkbox").prop('disabled', true);
            $(`#select-methods #${this.id}`).prop('disabled', false);
            $(`#select-methods #fdr`).prop('disabled', false);
            // Hide tab for the current method and the disabled methods
            $(`a#tasktable-tab`).hide();
        }
        else if( this.id == "sanxot" ) {
            // Hide tab for the current method and the disabled methods
            $(`a#tasktable-tab`).hide();
        }
    }
});
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