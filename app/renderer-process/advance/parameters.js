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
    // pRatio ------
    // add ncpu
    parametor.addParamsInMethod(data["workflow"]["rules"], [0], [0], `--n_workers ${document.querySelector('#nthreads').value}`);
    if (document.querySelector('#deltaMassThreshold')) {
        let val = document.querySelector('#deltaMassThreshold').value;
        parametor.addParamsInMethod(data["workflow"]["rules"], [0], [0], `--threshold ${val}`);
    }
    if (document.querySelector('#deltaMassAreas')) {
        let val = document.querySelector('#deltaMassAreas').value;
        parametor.addParamsInMethod(data["workflow"]["rules"], [0], [0], `--jump_areas ${val}`);
    }
    if (document.querySelector('#tagDecoy')) {
        let val = document.querySelector('#tagDecoy').value;
        parametor.addParamsInMethod(data["workflow"]["rules"], [0], [0], `--lab_decoy ${val}`);
    }
    if (document.querySelector('#hot')) {
        // get the list of unique experiments
        let tasktable = $("#hot").data('handsontable')
        let expts = tasktable.getDataAtCol(0).filter(unique);
        let val = expts.sort().join(",");
        parametor.addParamsInMethod(data["workflow"]["rules"], [0], [0], `--expt ${val}`);
    }

    return data
} // end addParams

function createParameters(conf) {
    let params = {};

    // get input directory
    let indir = parametor.getInFileDir('indir');
    if ( !indir ) {
        exceptor.showMessageBox('Error Message', 'Input directory is required');
        return false;
    }
    else { params.indir = indir }
    // get and create check and get: output directory
    let outdir = parametor.createLocalDir('outdir');
    if ( !outdir ) {
        exceptor.showMessageBox('Error Message', 'Output directory is required');
        return false;
    }
    else { params.outdir = outdir }
    // create tasktable file
    let dtablefile = parametor.createtasktableFile(outdir); 
    if ( !dtablefile ) {
        exceptor.showMessageBox('Error Message', 'Creating tasktable file');
        return false;
    }
    // create category file
    let catfile = parametor.getInFileDir('catfile');
    if ( !catfile ) {
        exceptor.showMessageBox('Error Message', 'Category file is required');
        return false;
    }
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

