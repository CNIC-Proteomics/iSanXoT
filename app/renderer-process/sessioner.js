/*
  Global variables
*/
const { ipcRenderer } = require('electron');
let psTree = require(`${process.env.ISANXOT_LIB_HOME}/node/node_modules/ps-tree`);

// Add the list of processes into the list session
function addProcToSession(a_pids, wf) {
    // extract the session info
    let pids = JSON.parse( window.sessionStorage.getItem("pids") );
    // create list of data
    if ( pids === null ) { // init        
        pids = [a_pids];
    }
    else {
        // concatenate. create a list of list with the all processes
        pids.push(a_pids);
    }
    // save session info
    window.sessionStorage.setItem("pids", JSON.stringify(pids));
    // send the list of pids
    ipcRenderer.send('send-pids', {
        'pids': pids
    });
};

// Save the process id in the session storage
function addProcessesToSession(pid, log, wfname, page=false) {
    // when all the processes have been saved, then, we jump to another page
    var jumpToPage = function (page) {
        // go to procceses section
        if ( page ) {
            ipcRenderer.send('load-page', page);
        }
    }
    // save the whole list of process of ids at the moment
    var addProcesses = function (pid, log, page, callback) {
        // get the children processes from the given main PID
        psTree(pid, function (err, children) {
            let pids = [log];
            for (var i = 0; i < children.length; i++) {
                let p = children[i];
                pids.push(p.PID);
            }
            // save the list of process ids at the moment
            addProcToSession(pids, wfname);
            callback(page);
        });
    };
    // call the function using the callback
    addProcesses(pid, log, page, jumpToPage);
};

// We exports the modules
module.exports = {
    addProcessesToSession: addProcessesToSession
};
