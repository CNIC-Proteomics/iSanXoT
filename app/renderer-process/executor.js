/*
 * Import libraries
 */

let fs = require('fs');
let path = require('path');
let cProcess = require('child_process');

let exceptor = require('./exceptor');
let sessioner = require('./sessioner');
var projector = module.parent.exports; // avoiding circular dependencies with Node require()
// let projector = require('./projector');
// let workflower = require('./workflower');

var proc = null;


/*
 * Local functions
 */


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

function execProcess(script, cmd, cfg, log, wfname) {
    // eexecute command line
    console.log(cmd);
    proc = cProcess.exec(cmd);

    // save the process id in the session storage
    sessioner.addProcessesToSession(proc.pid, cfg, log, wfname, `${__dirname}/../processes.html`);

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
    let intpl = `${path.join(process.env.ISANXOT_WFS_HOME, 'tpl_commands')}`;
    let cmd = `"${process.env.ISANXOT_PYTHON_EXEC}" "${path.join(process.env.ISANXOT_WFS_HOME, 'table2cfg.py')}" \
    --attfile "${params.attfile}" \
    --indir "${params.indir}" \
    --intpl "${intpl}" \
    --outfile "${params.outfile}" 1> "${params.logdir}/table2cfg.log" `;
    execSyncProcess('creating config files', cmd);    
};

function execSnakeMake(params) {
    let smkfile = `${path.join(process.env.ISANXOT_WFS_HOME, 'wf_sanxot.smk')}`;
    let cmd_smk = `"${process.env.ISANXOT_PYTHON_EXEC}" "${path.join(process.env.ISANXOT_WFS_HOME, 'mysnake.py')}" \
    --configfile "${params.configfile}" \
    --snakefile "${smkfile}" \
    --cores ${params.nthreads} \
    --directory "${params.directory}" `;
    let cmd = `${cmd_smk} 1> "${params.logfile}" 2>&1`;
    execProcess('executing the workflow', cmd, params.configfile, params.logfile, params.directory);
};

// execute project
function executeProject() {
    // save project
    let [prj_id, prj_dir, dte_dir] = projector.saveProject();
    // prepare the workspace of project
    let log_dir = projector.preparePrjWorkspace(prj_id, prj_dir);
    // Execute snakemake
    execSnakeMake({
        'configfile': `${dte_dir}/config.yaml`,
        'nthreads':   `${document.querySelector('#nthreads').value}`,
        'directory':  `${prj_dir}`,
        'logfile':    `${log_dir}/isanxot.log`
    });
};

/*
 * Events
 */
// Execute process
if ( document.querySelector('#executor #start') !== null ) {
    document.querySelector('#executor #start').addEventListener('click', function() {
        // loading...
        exceptor.loadingWorkflow();
        setTimeout(function() {
            // Execute the workflow
            executeProject();
        }, 1000); // due the execSync block everything, we have to wait until loading event is finished
    });
}

module.exports = {
    // saveProject: saveProject
    execTable2Cfg: execTable2Cfg
};