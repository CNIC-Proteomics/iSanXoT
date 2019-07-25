/*
  Global variables
*/
const { ipcRenderer } = require('electron');
let cProcess = require('child_process');
let psTree = require(process.env.ISANXOT_NODE_PATH + '/ps-tree');
let proc = null;

window.onbeforeunload = function(e) {
    // extract the session info
    let pids = JSON.parse( window.sessionStorage.getItem("pids") );
    let logs = JSON.parse( window.sessionStorage.getItem("logs") );
    // refresh the ids of child process from the pids
    if ( pids !== null ) {
        let c_pids = [];
        for (var i = 0; i < pids.length; i++) { 
            let pid = parseInt(pids[i]);
            let c_pid = [];
            psTree(pid, function (err, children) {
                children.forEach(function (p) {
                    c_pid.push(p.PID);
                });
            });
            // c_pids.push(c_pid);
        }
        // // save session info
        // window.sessionStorage.setItem("c_pids", JSON.stringify(c_pids));
        // // create the processes structure
        // let procs = {
        //     'pids': pids,
        //     'c_pids': c_pids,
        //     'logs': logs
        // }
        // // send the processes structure to to main js
        // ipcRenderer.send('send-pids', procs);
    }
};

// Add info to session
function addProcToSession(pid, log) {
    // extract the session info
    let pids = JSON.parse( window.sessionStorage.getItem("pids") );
    let logs = JSON.parse( window.sessionStorage.getItem("logs") );
    // create list of data
    if ( pids === null ) { // init        
        pids = [pid];
        logs = [log];
    }
    else {
        ipcRenderer.send('send-pid', pid);
        pids.push(pid);
        logs.push(log);
    }
    // save session info
    window.sessionStorage.setItem("pids", JSON.stringify(pids));
    window.sessionStorage.setItem("logs", JSON.stringify(logs));
};

// Save the process id in the session storage
function addProcessesToSession(pid, log) {
    // the actual pid is for the CMD (shell). Then...
    // get the pid for the first child process => the script pid
    psTree(pid, function (err, children) {
        // children.forEach(function (p, i) {
        for (var i = 0; i < children.length; i++) {
            let p = children[i];
            console.log(`${i} => ${p.PID}`);
            if ( i == 0) {
                console.log(p.PID);
                // save the process id in the session storage
                addProcToSession(p.PID, log)
                // go to procceses section
                // ipcRenderer.send('load-page', `${__dirname}/../processes.html`);
                break;
            }
        }
        // });
    });
};

// Exec process
function execProcess(cmd, log) {
    // eexecute command line
    proc = cProcess.exec(cmd);

    // save the process id in the session storage
    addProcessesToSession(proc.pid, log);

    // Handle on stderr
    proc.stderr.on('data', (data) => {
      console.log(`stderr: ${data}`);
    });
  
    // Handle on exit event
    proc.on('close', (code) => {
        var preText = `Child exited with code ${code} : `;
        // switch(code){
        //     case 0:
        //         console.info(preText+"Something unknown happened executing the batch.");
        //         break;
        //     case 1:
        //         console.info(preText+"The file already exists");
        //         break;
        //     case 2:
        //         console.info(preText+"The file doesn't exists and now is created");
        //         break;
        //     case 3:
        //         console.info(preText+"An error ocurred while creating the file");
        //         break;
        // }
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
      // Check and retrieves parameters depending on the type of workflow
      let params = importer.parameters.createParameters(cfgfile);
      if ( params ) {
        // Execute the workflow
        let cmd_smk = `"${process.env.ISANXOT_PYTHON3x_HOME}/tools/Scripts/snakemake.exe" --configfile "${params.cfgfile}" --snakefile "${smkfile}" --cores ${params.nthreads} --directory "${params.outdir}"`;
        // let cmd = `${cmd_smk} --unlock && ${cmd_smk} --rerun-incomplete > "${params.logfile}" 2>&1`;
        let cmd1 = `${cmd_smk} --unlock`;
        let cmd2 = `${cmd_smk} --rerun-incomplete > "${params.logfile}" 2>&1`;
        // Sync process that Unlock the output directory
        // First we unlock the ouput directory
        console.log(cmd1);
        cProcess.execSync(cmd1);
        // Then, we execute the workflow
        console.log(cmd2);
        execProcess(cmd2, params.logfile);
      }
    });
}

// Kill processes
if ( document.querySelector('#processor #stop') !== null ) {
    document.querySelector('#processor #stop').addEventListener('click', function() {
    //   if ( proc !== null ) {
    //     console.log(`Look for child processes from sms ${proc.pid}`);
    //     // appendToDroidOutput("\n\nThe processes have been stopped!\n\n");
    //     psTree(proc.pid, function (err, children) {  // check if it works always
    //       children.forEach(function (p) {
    //         console.log(`${p.PID} sub-process from ${proc.pid} has been killed!`);
    //         // process.kill(p.PID); 
    //       });
    //       // kill the main process
    //       console.log(`${proc.pid} has been killed!`);
    //       //process.kill(proc.pid);
    //     });
    //   }
    });
}