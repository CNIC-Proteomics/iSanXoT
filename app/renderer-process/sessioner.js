/*
  Global variables
*/
const { ipcRenderer } = require('electron');
let psTree = require(`${process.env.ISANXOT_LIB_HOME}/node/node_modules/ps-tree`);

// Add info to session
function addProcToSession(pid, log, wf) {
    // extract the session info
    let pids = JSON.parse( window.sessionStorage.getItem("pids") );
    let logs = JSON.parse( window.sessionStorage.getItem("logs") );
    let wfs  = JSON.parse( window.sessionStorage.getItem("wfs") );
    // create list of data
    if ( pids === null ) { // init        
        pids = [pid];
        logs = [log];
        wfs  = [wf];
    }
    else {
        ipcRenderer.send('send-pid', pid);
        pids.push(pid);
        logs.push(log);
        wfs.push(wf);
    }
    // save session info
    window.sessionStorage.setItem("pids", JSON.stringify(pids));
    window.sessionStorage.setItem("logs", JSON.stringify(logs));
    window.sessionStorage.setItem("wfs",  JSON.stringify(wfs));
};

// Save the process id in the session storage
function addProcessesToSession(pid, log, wfname, page=false) {
    // the actual pid is for the CMD (shell). Then...
    // get the pid for the first child process => the script pid
    psTree(pid, function (err, children) {
        for (var i = 0; i < children.length; i++) {
            let p = children[i];
            console.log(`${i} => ${p.PID}`);
            if ( i == 0) {
                console.log(p.PID);
                // save the process id in the session storage
                addProcToSession(p.PID, log, wfname)
                // go to procceses section
                if ( page ) {
                    // ipcRenderer.send('load-page', `${__dirname}/../processes.html`);
                    ipcRenderer.send('load-page', page);
                }
                break;
            }
        }
    });
};

// We exports the modules
module.exports = {
    addProcessesToSession: addProcessesToSession
};
