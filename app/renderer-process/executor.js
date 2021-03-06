/*
 * Import libraries
 */
let exceptor = require('./exceptor');
let importer = require('./imports');
let sessioner = require('./sessioner');
let fs = require('fs');
let crypto = require('crypto');
let path = require('path');
let cProcess = require('child_process');
var proc = null;


/*
 * Local functions
 */

// Prepare  the workspace of a project
function preparePrjWorkspace(date_id, outdir, prj_dirs) {
    // declare variables
    let cfg_dir = `${outdir}/.isanxot`;
    let dte_dir = `${cfg_dir}/${date_id}`;
    let log_dir = `${outdir}/${prj_dirs['logdir']}/${date_id}`;
    // check the output directory
    if ( outdir == "" ) {
        exceptor.showMessageBox('error',`The output directory is empty`, title='Extract output directory', end=true);
    }
    // create the directories for the project
    for ( let k in prj_dirs ) {
        let ws = prj_dirs[k];
        let prj_dir = `${outdir}/${ws}`;
        try {
            if ( !fs.existsSync(`${prj_dir}`) ) {
                fs.mkdirSync(`${prj_dir}`, {recursive: true} );
            }
        } catch (err) {    
            console.log(prj_dir);
            exceptor.showMessageBox('error',`${prj_dir}: ${err}`, title='Creating directory', end=true);
        }    
    }
    // create configuration directory (hidden) for the current execution    
    try {
        if ( !fs.existsSync(`${dte_dir}`) ) {
            fs.mkdirSync(`${dte_dir}`, {recursive: true} );
        }
    } catch (err) {    
        console.log(dte_dir);
        exceptor.showMessageBox('error',`${dte_dir}: ${err}`, title='Creating config directory', end=true);
    }
    // create log directory for the current execution
    try {
        if ( !fs.existsSync(`${log_dir}`) ) {
            fs.mkdirSync(`${log_dir}`, {recursive: true} );
        }
    } catch (err) {    
        console.log(log_dir);
        exceptor.showMessageBox('error',`${log_dir}: ${err}`, title='Creating logging directory', end=true);
    }
    return [cfg_dir, dte_dir, log_dir];
}
// Export tasktable to TSV
function exportTasktable(tsk_id, header) {
    // rename header
    $(`${tsk_id}`).handsontable('updateSettings', {'colHeaders': header });
    let exportPlugin = $(`${tsk_id}`).handsontable('getPlugin', 'exportFile');
    let cont = exportPlugin.exportAsString('csv', {
        mimeType: 'text/csv',
        columnDelimiter: '\t',
        columnHeaders: true,
        exportHiddenColumns: true,
        bom: false
    });
    return cont;
}

function createConfigFiles(date_id, outdir, dte_dir, wf) {
    // Create config file with basic parameters of workflow
    let cfg = {
        'name': wf['id'],                
        'version': require('electron').remote.app.getVersion(),
        'date': date_id,
        'ncpu': document.querySelector('#nthreads').value,
        'verbose': '-vv'
    };
    // add the directories for the project
    cfg['prj_workspace'] = {};
    for (var ws in wf['prj_workspace']) {
        cfg['prj_workspace'][ws] = `${outdir}/${wf['prj_workspace'][ws]}`;
    }
    // add the main_inputs
    cfg['main_inputs'] = createObjFromMainInputsPanel(); // function in the panel section
    // add the databases
    cfg['databases'] = createObjFromDatabasesPanel(); // function in the panel section
    // Create a tasktable for every work
    // Add the files into config file
    // Iterate over all the works of the workflow
    cfg['datfiles'] = [];
    for (var i = 0; i < wf['works'].length; i++) {
        let wk = wf['works'][i];
        let wk_id = wk['id'];
        let dte_file = `${dte_dir}/${wk['file']}`;
        let cont = '';
        let header = null;
        cfg['datfiles'].push({
            'type': wk_id,
            'file': dte_file
        });
        // Concatenate the data table of all commands
        // Iterate over all commands
        for (var j = 0; j < wk['cmds'].length; j++) {
            let cmd = wk['cmds'][j];
            let cmd_id = cmd['id'];
            // replace if we have information from the wortkflow.json config file. DropDown objects with the command
            try {
                // get the attributes of command from the local file (JSON)
                let cmd_attr = importer.getObjectFromID(wk['cmds'], cmd_id);
                // get the index of DropDown parameters
                let [cmd_params_hottable_index, cmd_params_hottable] = importer.getIndexParamsWithKey(cmd_attr['params'], 'hottable');
                // replace if we have information from the wortkflow.json config file. DropDown objects with the command
                if (cmd_params_hottable && cmd_params_hottable.length > 0) {                   
                    // get the number of row from given table of command
                    let nrows = $(`#${wk_id} #page-tasktable-${cmd_id} .tasktable`).handsontable('countRows');
                    // replace the key by the values for all the rows from the given column
                    // look throught the different hottable replacements by column
                    // look throught all the rows of the command table
                    for (var ncol in cmd_params_hottable) {
                        let rep = cmd_params_hottable[ncol].data;
                        for (var nrow = 0; nrow < nrows; nrow++) {
                            let k = $(`#${wk_id} #page-tasktable-${cmd_id} .tasktable`).handsontable('getDataAtCell', parseInt(nrow), parseInt(ncol));
                            let new_v = rep[k];
                            $(`#${wk_id} #page-tasktable-${cmd_id} .tasktable`).handsontable('setDataAtCell', parseInt(nrow), parseInt(ncol), new_v);
                        }
                    }

                }
            } catch (err) {
                exceptor.showErrorMessageBox('Error Message', `Replacing the values of labels in the command table ${cmd_id}: ${err}`, end=true);    
            }
            // get the id header based on 'workflow.json'
            try {
                header = cmd['params'].map(a => a.id);
                if (header.includes(undefined)) {
                    throw "the list of id headers contains undefined value";
                }
            } catch (err) {
                exceptor.showErrorMessageBox('Error Message', `Extracting the id headers of ${cmd_id}: ${err}`, end=true);
            }
            // export tasktable to CSV
            try {
                cont += `\n#${cmd_id}\n`;
                cont += exportTasktable(`#${wk_id} #page-tasktable-${cmd_id} .tasktable`, header);
            } catch (err) {
                exceptor.showErrorMessageBox('Error Message', `Exporting the command table ${cmd_id}: ${err}`, end=true);    
            }
            // write file sync
            try {
                fs.writeFileSync(dte_file, cont, 'utf-8');
            } catch (err) {    
                exceptor.showErrorMessageBox('Error Message', `Writing the tasktable file ${dte_file}: ${err}`, end=true);    
            }
            // come back the names in the columns
            // get the id header based on 'workflow.json'
            try {
                let header_names = cmd['params'].map(a => a.name);
                if (header_names.includes(undefined)) {
                    throw "the list of id headers contains undefined value";
                }
                // rename column headers   
                $(`#${wk_id} #page-tasktable-${cmd_id} .tasktable`).handsontable('updateSettings',{'colHeaders': header_names });
            } catch (err) {
                exceptor.showErrorMessageBox('Error Message', `Extracting the names headers of ${cmd_id}: ${err}`, end=true);
            }
        }
    }
    let cfgfile = `${dte_dir}/.cfg.yaml`;
    let cfgcont = jsyaml.safeDump(cfg);
    // write file sync
    try {
        fs.writeFileSync(cfgfile, cfgcont, 'utf-8');
    } catch (err) {    
        exceptor.showErrorMessageBox('Error Message', `Writing the config file ${cfgfile}: ${err}`, end=true);    
    }
    return cfgfile;
}

function checksum(str, algorithm, encoding) {
    return crypto
        .createHash(algorithm || 'md5')
        .update(str, 'utf8')
        .digest(encoding || 'hex')
}
function copyDiffFiles(srcDir, tgtDir) {
    let srcFiles = fs.readdirSync(srcDir);
    srcFiles.forEach( function (srcFile) {
        srcFile = `${srcDir}/${srcFile}`;
        let srcCont = fs.readFileSync(srcFile, "utf-8");
        let tgtFile = `${tgtDir}/${path.basename(srcFile)}`;
        if ( fs.existsSync(tgtFile) ) {
            let tgtCont = fs.readFileSync(tgtFile, "utf-8");
            let srcCS = checksum(srcCont);
            let tgtCS = checksum(tgtCont);
            if (srcCS != tgtCS ) {
                fs.writeFileSync(tgtFile, srcCont);
            }
        } else {
            fs.writeFileSync(tgtFile, srcCont);
        }
    } );
};

// function copyFileSync( source, target ) {
//     // if target is a directory a new file with the same name will be created
//     let targetFile = target;
//     if ( fs.existsSync( target ) ) {
//         if ( fs.lstatSync( target ).isDirectory() ) {
//             targetFile = path.join( target, path.basename( source ) );
//         }
//     }
//     fs.writeFileSync(targetFile, fs.readFileSync(source));
// }
// function copyFolderRecursiveSync( source, target ) {
//     // check if folder needs to be created or integrated
//     let targetFolder = target;
//     if ( !fs.existsSync( targetFolder ) ) {
//         fs.mkdirSync( targetFolder );
//     }

//     //copy
//     if ( fs.lstatSync( source ).isDirectory() ) {
//         let files = [];
//         files = fs.readdirSync( source );
//         files.forEach( function ( file ) {
//             var curSource = path.join( source, file );
//             if ( fs.lstatSync( curSource ).isDirectory() ) {
//                 copyFolderRecursiveSync( curSource, targetFolder );
//             } else {
//                 copyFileSync( curSource, targetFolder );
//             }
//         } );
//     }
// }

// Exec process
function execSyncProcess(script, cmd) {
    try {
        console.log(cmd);
        proc = cProcess.execSync(cmd);
    } catch (ex) {
        console.log(`stderr: ${script}: ${ex.stderr.toString()} \n ${ex.message}`);
        exceptor.stopLoadingWorkflow();
        exceptor.showErrorMessageBox(`${script}`, `${ex.stderr.toString()}`, end=true);
    }
};

function execProcess(script, cmd, log, wfname) {
    // eexecute command line
    console.log(cmd);
    proc = cProcess.exec(cmd);

    // save the process id in the session storage
    sessioner.addProcessesToSession(proc.pid, log, wfname, `${__dirname}/../processes.html`);

    // Handle on stderr
    proc.stderr.on('data', (data) => {
        console.log(`stderr: ${data}`);
        exceptor.stopLoadingWorkflow();
        exceptor.showErrorMessageBox(`${script}`, `${data}`, end=true);
    });
  
    // Handle on exit event
    proc.on('close', (code) => {
        console.log(`Child exited with code ${code}`);
        exceptor.stopLoadingWorkflow();
    });  
};

function execTable2Cfg(params) {
    let intpl = `${process.env.ISANXOT_SRC_HOME}/wfs/tpl_commands.yaml`;
    let cmd = `"${process.env.ISANXOT_LIB_HOME}/python/tools/python" "${process.env.ISANXOT_SRC_HOME}/wfs/table2cfg.py" \
    --attfile "${params.attfile}" \
    --indir "${params.indir}" \
    --intpl "${intpl}" \
    --outfile "${params.outfile}" 1> "${params.logdir}/table2cfg.log" `;
    execSyncProcess('creating config files', cmd);    
};
function execSnakeMake(params) {
    let smkfile = `${process.env.ISANXOT_SRC_HOME}/wfs/wf_sanxot.smk`;
    let cmd_smk = `"${process.env.ISANXOT_LIB_HOME}/python/tools/python" "${process.env.ISANXOT_SRC_HOME}/wfs/mysnake.py" \
    --configfile "${params.configfile}" \
    --snakefile "${smkfile}" \
    --cores ${params.nthreads} \
    --directory "${params.directory}" `;
    let cmd = `${cmd_smk} 1> "${params.logfile}" 2>&1`;
    execProcess('executing the workflow', cmd, params.logfile, params.directory);
}
/*
 * Events
 */
// Execute process
if ( document.querySelector('#executor #start') !== null ) {
    document.querySelector('#executor #start').addEventListener('click', function() {
        // loading...
        exceptor.loadingWorkflow();
        // Execute the workflow
        executeProject();
    });
}

/*
 * Export functions
 */


// save project
function saveProject(wf_date_id, wf) {
    // get the output directory
    let outdir = $(`#main_inputs #outdir`).val();
    // prepare the workspace of project
    let [cfg_dir, dte_dir, log_dir] = preparePrjWorkspace(wf_date_id, outdir, wf['prj_workspace']);
    // create datafiles
    let attfile = createConfigFiles(wf_date_id, outdir, dte_dir, wf);
    // Exec: create config file for the execution of workflow
    execTable2Cfg({
        'indir': dte_dir,
        'attfile': attfile,
        'outfile': `${dte_dir}/config.yaml`,
        'logdir': log_dir
    });
    // Copy only the files that are different
    copyDiffFiles(`${dte_dir}`, `${cfg_dir}`);
    return [outdir, cfg_dir, dte_dir, log_dir, attfile];
};
// execute project
function executeProject() {
    setTimeout(function() {
        // imported variables
        let wf = importer.wf;
        let wf_date_id = importer.wf_date_id;
        if ( wf_date_id && wf ) {
            // save project
            let [outdir, cfg_dir, dte_dir, log_dir, attfile] = saveProject(wf_date_id, wf);
            // Execute snakemake
            execSnakeMake({
                'configfile': `${outdir}/.isanxot/config.yaml`,
                'nthreads':   `${document.querySelector('#nthreads').value}`,
                'directory':  `${outdir}`,
                'logfile':    `${log_dir}/isanxot.log`
            });
        }
        else {
            exceptor.showMessageBox('error', "The workflow identifier is not defined", title='No project to execute', end=true);
        }
    }, 1000); // due the execSync block everything, we have to wait until loading event is finished
};
module.exports = {
    saveProject: saveProject
};