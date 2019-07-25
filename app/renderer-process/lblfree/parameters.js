/*
 * Handle parameters
 */
let parametor = require('../parameters');
let exceptor = require('../exceptor');


function addParams(data) {
    // discard outliers -----
    // add tags into 'peptide2protein' for the sanxot2
    // add tags into 'proteinExpto2all' for the sanxot2
    if ( document.querySelector('#discardOutliers') && document.querySelector('#discardOutliers').checked ) {
        parametor.addParamsInMethod(data["workflow"]["rules"], [5], [2], `--tags="!out"`)
        parametor.addParamsInMethod(data["workflow"]["rules"], [11], [2], `--tags="!out"`)
    }
    // converter ------
    // add ncpu
    parametor.addParamsInMethod(data["workflow"]["rules"], [0], [0], `--n_workers ${document.querySelector('#nthreads').value}`);

    return data
} // end addParams

function createParameters(conf) {
    let params = {};

    // get input file
    let infile = parametor.getInFileDir('infile');
    if ( !infile ) {
        exceptor.showMessageBox('Error Message', 'Input file is required');
        return false;
    }
    else { params.infile = infile }
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
    // create db file
    let dbfile = parametor.getInFileDir('dbfile');
    if ( !dbfile ) {
        exceptor.showMessageBox('Error Message', 'Database file is required');
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
        'infile': infile,
        'outdir': outdir,
        'tskfile': dtablefile,
        'catfile': catfile,
        'dbfile': dbfile
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

