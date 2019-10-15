/*
 * Handle parameters
 */
let parametor = require('../parameters');
let exceptor = require('../exceptor');


function addParams(data) {
    const unique = (value, index, self) => {
        return self.indexOf(value) === index && value !== null;
    };
    // discard outliers -----
    // add tags into 'scan2peptide', peptide2protein','protein2category' for sanxot1 and sanxot2
    if ( document.querySelector('#discardOutliers') && document.querySelector('#discardOutliers').checked ) {
        parametor.addParamsInMethod(data["workflow"]["rules"], [4,5,6], [0,2], `--tags="!out"`)
    }
    return data
} // end addParams

function createParameters(conf) {
    let params = {};

    // REQUIRED: get input directory
    let indir = parametor.getInFileDir('indir');
    if ( !indir ) {
        exceptor.showMessageBox('Error Message', 'Input directory is required');
        return false;
    }
    else { params.indir = indir }
    // REQUIRED: get and create check and get: output directory
    let outdir = parametor.createLocalDir('outdir');
    if ( !outdir ) {
        exceptor.showMessageBox('Error Message', 'Output directory is required');
        return false;
    }
    else { params.outdir = outdir }
    // OPTIONAL: create tasktable file
    let dtablefile = parametor.createtasktableFile(outdir); 
    // if ( !dtablefile ) {
    //     exceptor.showMessageBox('Error Message', 'Creating tasktable file');
    //     return false;
    // }
    // OPTIONAL: create category file
    let catfile = parametor.getInFileDir('catfile');
    // if ( !catfile ) {
    //     exceptor.showMessageBox('Error Message', 'Category file is required');
    //     return false;
    // }
    // create the config data
    let cfgdata = parametor.createConfData(conf, {
        'indir': indir,
        'outdir': outdir,
        'tskfile': dtablefile,
        'catfile': catfile
    }, addParams);
    if ( !cfgdata ) {
        exceptor.showMessageBox('Error Message', 'Creating config data');
        return false;
    }
    // Enable-Disable methods
    cfgdata = parametor.endisConfMethod(cfgdata);
    if ( !cfgdata ) {
        exceptor.showMessageBox('Error Message', 'All methods are disabled');
        return false;
    }
    // Create Config file
    let [cfgfile, logfile] = parametor.createConfFile(cfgdata, outdir);
    if ( !cfgfile ) {
        exceptor.showMessageBox('Error Message', 'Creating config file');
        return false;
    }
    else {
        params.cfgfile = cfgfile;
        params.logfile = logfile;
    }
    // get: num threads
    params.nthreads = document.querySelector('#nthreads').value;


    return params;
}

// Export modules
module.exports.createParameters = createParameters;

/*
 * Events for the local parameters
 */

function enable_checkbox_method(id) {
    $(`${id}`).prop('disabled', false);
    $(`${id}`).prop('checked', true);
}
function disable_checkbox_method(id) {
    $(`${id}`).prop('disabled', true);
    $(`${id}`).prop('checked', false);
}
function accept_parameter(id) {
    $(`div[name="${id}"]`).show();
    $(`#${id}`).attr("discard",false);
}
function discard_parameter(id) {
    $(`div[name="${id}"]`).hide();
    $(`#${id}`).attr("discard",true);
}

$("#select-methods :checkbox").on("change", function(){
    if($(this).is(":checked")){
        // Enable methods
        $("#select-methods :checkbox").prop('disabled', false);
        if( this.id == "fdr" ) {
            // enable the other methods
            // enable_checkbox_method(`#select-methods #ratios`);
            // enable_checkbox_method(`#select-methods #sanxot`);
            // Show tab for the current method
            $('a#params-pratio-tab').show();
        }
        else if( this.id == "ratios" ) {
            // enable the other methods
            // enable_checkbox_method(`#select-methods #sanxot`);
            // Show tab for the current method
            $('a#tasktable-tab').show();
            // Accept the following parameters
            accept_parameter('hot');
        }
        else if( this.id == "sanxot" ) {
            // Show tab for the current method
            $('a#tasktable-tab').show();
            // Accept the following parameters
            accept_parameter('select-catfile');
            accept_parameter('catfile');
        }
    }
    else if($(this).is(":not(:checked)")) {
        // Disable methods depending on which one
        if( this.id == "fdr" ) {
            // disaable the other methods
            disable_checkbox_method(`#select-methods #ratios`);
            disable_checkbox_method(`#select-methods #sanxot`);
            // Hide tab for the current method and the disabled methods
            $(`a#params-pratio-tab`).hide();
            // Discard the following parameters
            discard_parameter('hot');
        }
        else if( this.id == "ratios" ) {
            // disaable the other methods
            disable_checkbox_method(`#select-methods #sanxot`);
            // Hide tab for the current method and the disabled methods
            $(`a#tasktable-tab`).hide();
            // Discard the following parameters
            discard_parameter('select-catfile');
            discard_parameter('catfile');
        }
        else if( this.id == "sanxot" ) {
            // Hide tab for the current method and the disabled methods
            // $(`a#tasktable-tab`).hide();
            // Discard the following parameters
            discard_parameter('select-catfile');
            discard_parameter('catfile');
        }
    }
});
