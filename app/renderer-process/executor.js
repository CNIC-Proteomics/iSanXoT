/*
  Global variables
*/
let importer = require('./imports');
let exceptor = require('./exceptor');
let sessioner = require('./sessioner');
let path = require('path');
let cProcess = require('child_process');
let proc = null;


// Exec process
function execSyncProcess(cmd) {
    try {
        console.log(cmd);
        proc = cProcess.execSync(cmd);
    } catch (ex) {
        console.log(`stderr: ${ex.error}`);
        exceptor.stopLoadingWorkflow();
        exceptor.showMessageBox('Error Message', `${ex.error}`);
    }
};

function execProcess(cmd, log, wfname) {
    // eexecute command line
    console.log(cmd);
    proc = cProcess.exec(cmd);

    // save the process id in the session storage
    sessioner.addProcessesToSession(proc.pid, log, wfname, `${__dirname}/../processes.html`);

    // Handle on stderr
    proc.stderr.on('data', (data) => {
        console.log(`stderr: ${data}`);
        exceptor.stopLoadingWorkflow();
        exceptor.showMessageBox('Error Message', `${data}`);
    });
  
    // Handle on exit event
    proc.on('close', (code) => {
        console.log(`Child exited with code ${code}`);
        exceptor.stopLoadingWorkflow();
    });  
};


/*
 * Events
 */
// Execute process
if ( document.querySelector('#executor #start') !== null ) {
    document.querySelector('#executor #start').addEventListener('click', function() {
        // get the type of Workflow
        let smkfile = importer.tasktable.smkfile;
        let cfgfile = importer.tasktable.cfgfile;
        // get the name of workflow
        let wfname = path.basename(cfgfile, '.json');
        // Check and retrieves parameters depending on the type of workflow
        let params = importer.parameters.createParameters(cfgfile);
        if ( params ) {
            // loading...
            exceptor.loadingWorkflow();
            // Execute the workflow
            setTimeout(function() {
                let cmd_smk    = `"${process.env.ISANXOT_PYTHON3x_HOME}/tools/Scripts/snakemake.exe" --configfile "${params.cfgfile}" --snakefile "${smkfile}" --cores ${params.nthreads} --directory "${params.outdir}" --rerun-incomplete`;
                let cmd_unlock = `${cmd_smk} --unlock `;
                let cmd_clean  = `${cmd_smk}  --cleanup-metadata "${smkfile}"`;
                // Sync process that Unlock the output directory
                // First we unlock the ouput directory
                let cmd1 = `${cmd_unlock} && ${cmd_clean}`
                execSyncProcess(cmd1);
                // Then, we execute the workflow
                let cmd2 = `${cmd_smk} > "${params.logfile}" 2>&1`;
                execProcess(cmd2, params.logfile, wfname);    
            }, 1000); // due the execSync block everything, we have to wait until loading event is finished
        }
    });
}