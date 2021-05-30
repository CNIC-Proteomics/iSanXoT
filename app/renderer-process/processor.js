/*
 * Import libraries
 */

let psTree = require(`${process.env.ISANXOT_LIB_HOME}/node/node_modules/ps-tree`);
let fs = require('fs');
const { ipcRenderer } = require('electron');
const { dialog } = require('electron').remote

let importer = require('./imports');
let exceptor = require('./exceptor');
let logger = require('./logger');

let logObject = undefined;
let timeOut = undefined;


/*
 * Main
 */


window.onload = function(e) {
    // stop loading workflow
    exceptor.stopLoadingWorkflow();

    // send the new Child Process to IPC Render and save into Session calling callback function
    sendChildProcesses();

    // create the list of log data based on the session info: pids and current outdir
    let status = 1; // init the status
    let ldata = []; // refresh the ids of child process from the pids

    // get the list of PIDs running
    let pids = JSON.parse( window.sessionStorage.getItem("pids") );
    if ( pids !== null ) {
        for (var i = 0; i < pids.length; i++) {
            let cfgfile = pids[i][0];
            let logfile = pids[i][1];
            let pid = parseInt(pids[i][2]);
            let c_pids = pids[i].slice(3);
            ldata.push({
                'pid': pid,
                'c_pids': c_pids.join(","),
                'status': status,
                'cfgfile': cfgfile,
                'logfile': logfile,
            });
        }
    }

    // get the outdir of the current project
    let outdir = window.sessionStorage.getItem("outdir");
    if ( outdir !== null ) {
        // get the files/dirs in directory sorted by name
        let logdirs = importer.getDirectories(`${outdir}/logs`);
        let cfgdirs = importer.getDirectories(`${outdir}/.isanxot`);
        // get the intersection of two list. We need both files (logfile and config file)
        let comdirs = logdirs.filter(x => cfgdirs.indexOf(x) !== -1)
        // add only the files (logfile and config file) that have not already in the log-data
        for (let i = 0; i < comdirs.length; i++) {
            let cfgfile = `${outdir}/.isanxot/${comdirs[i]}/config.yaml`;
            let logfile = `${outdir}/logs/${comdirs[i]}/isanxot.log`;
            // get the list of index with the given attribute value to know if the files are in the log-data list
            let isinCfg = importer.getIndexParamsWithAttr(ldata, 'cfgfile', cfgfile);
            let isinLog = importer.getIndexParamsWithAttr(ldata, 'logfile', logfile);
            // if both files are not in log-data, we included.
            if ( isinCfg === undefined && isinLog === undefined ) {
                ldata.push({
                    'pid': '-',
                    'c_pids': '-',
                    'status': status,
                    'cfgfile': cfgfile,
                    'logfile': logfile,
                });    
            }
        }
    }

    // create logger object with the list of logdata
    logObject = new logger(ldata);

    // Add looping function
    refreshLogger();
};

// Before close the windows, send the processes ids
$(window).on('beforeunload',function() {

    // TODO!!!
    // THIS NOT WORKING BECAUSE THE ASYNC FUNCTION DOES NOT FINISH.
    // We have to convert this function to SYNC
    // send the new Child Process to IPC Render and save into Session
    // sendChildProcesses();
});

function sendChildProcesses() {
    // send the new Child Process to IPC Render and save into Session
    function sendCPIDs(list_pids) {
        // look throught the list of list of PIDs coming from the session varaible
        list_pids.forEach( function(pids, i) {
            let cfg = pids[0];
            let log = pids[1];
            let pid = pids[2];
            console.log(`get child_projectlogs from ${pid}`);
            pids.slice(3).forEach( function(c_pid) {
                // update the list of PIDs with the new child pids
                psTree(parseInt(c_pid), function (err, children) {
                    for (var i = 0; i < children.length; i++) {
                        let p = children[i];
                        console.log(`send c_pid: ${i} > ${p.PID}`);
                        ipcRenderer.send('send-cpid', {
                            'cpid': p.PID
                        });            
                    }
                });
            });    
        });
    };
    // update the list of processes with the new childs
    // extract the session info    
    let list_pids = JSON.parse( window.sessionStorage.getItem("pids") );
    if ( list_pids !== null ) {
        // send the new Child Process to IPC Render and save into Session calling callback function
        sendCPIDs(list_pids);
    }
};

function getSelectedRow(logtable) {
    let selRow = undefined, selIdx = undefined;
    // take into account the table has the restrinction only one row/column (selectionMode: 'single')
    let selRange = logtable.getSelected();
    if ( selRange !== undefined ) {
        selRange = selRange[0];
        let r = selRange[0], c = selRange[1], r2 = selRange[2], c2 = selRange[3];
        // get the data log of selected row
        if (r == r2) {
            // get data from selected selected row (PID project)
            selRow = logtable.getDataAtRow(r);
            selIdx = r;
        }
    }
    return [selRow,selIdx];
};

function refreshLogger() {
    // send the new Child Process to IPC Render and save into Session calling callback function
    sendChildProcesses();

    // if project has been selected, refresh the Workflow log table
    // get the data log of selected row
    let logtable = $("#projectlogs .logtable").data('handsontable');
    if (logtable !== undefined) {
        // get the selected Row
        let [selRow,selIdx] = getSelectedRow(logtable);
        if ( selRow !== undefined ) {
            // get data from selected selected row (PID project)
            let pid = selRow[0];
            let log_index = importer.getIndexParamsWithAttr(logObject.data, 'pid', pid);
            let logData = logObject.data[log_index];
            let logfile = logData.logfile;
            // get the log content
            let s = fs.readFileSync(logfile);
            let cont = s.toString();
            // update the log tables (project and workflow)
            logObject.updateLogDataFromLogFile(logData, cont);
            logObject.createWorkflowLogsTable(logData);
            // render log tables
            logObject.renderLogTables()
        }
        // if there is not selected row of project table, the project log is refresh only
        else {
            // update project log table
            // extract the session info
            let pids = JSON.parse( window.sessionStorage.getItem("pids") );
            // refresh the ids of child process from the pids
            if ( pids !== null ) {
                for (var i = 0; i < pids.length; i++) {
                    let logData = logObject.data[i];
                    let logfile = pids[i][1];
                    // get the log content
                    let s = fs.readFileSync(logfile);
                    let cont = s.toString();
                    // parse log file and update the data
                    logObject.updateLogDataFromLogFile(logData, cont);
                }
                // render log tables
                logObject.renderLogTables(logObject.data)
            }
        }
        // if all project's in the table has finished...
        // then stop the setTimeout
        // otherwise, set the time out
        let stopTimeOut = true;
        let statusProj = logtable.getDataAtCol(1);
        for (let i = 0; i < statusProj.length; i++) {
            if ( statusProj[i] != 'finished' ) {
                stopTimeOut = false;
                break;
            }
        }
        // then stop the setTimeout
        if ( stopTimeOut ) {
            clearTimeout(timeOut);
        // otherwise, set the time out
        } else {
            timeOut = setTimeout(refreshLogger, 10000);
        }
    }
}


/*
 * Events
 */

// Kill processes
if ( document.querySelector('#processor #stop') !== null ) {
    // kill process and subprocess of selected project
    document.querySelector('#processor #stop').addEventListener('click', function() {
        // get the data log of selected row
        let logtable = $("#projectlogs .logtable").data('handsontable');
        if (logtable !== undefined) {
            // get the selected Row
            let [selRow,selIdx] = getSelectedRow(logtable);
            if ( selRow !== undefined ) {
                let pid = selRow[0];
                // ask to user to kill the processes
                let options = {
                    type: 'question',
                    buttons: ['Yes', 'No'],
                    message: `Do you want to kill the process and subprocess of ${pid} project?`,
                  };
                let response = dialog.showMessageBoxSync(null, options);
                if ( response === 0 ) {
                    // we get the child processes from the list of pids (session variable)
                    // kill the all processes
                    // we start from the end (reverse)
                    let session_pids = JSON.parse( window.sessionStorage.getItem("pids") );
                    let pids = [];
                    for (let i = 0; i < session_pids.length; i++) {
                        if ( pid == session_pids[i][2]) {
                            pids = session_pids[i].slice(2);
                        }
                    }                
                    pids.reverse().forEach(function (pid) {
                        console.log(`Look for child processes from sms ${pid}`);
                        psTree(pid, function (err, children, callback) {  // check if it works always
                            children.forEach(function (p) { // kill the subprocesses
                                try {
                                    console.log(`${p.PID} sub-process from ${pid} has been killed!`);
                                    process.kill(p.PID);
                                } catch (e) {
                                    console.log(`error killing ${p.PID}: ${e}`);
                                }
                            });
                            try { // kill the main process
                                console.log(`${pid} has been killed!`);
                                process.kill(pid);
                            } catch (e) {
                                console.log(`error killing ${pid}: ${e}`);
                            }
                        });    
                    });
                    // indicated in the project log table that the project has been stopped
                    logObject.data[selIdx].status = "stopped";
                    // render log tables
                    logObject.renderLogTables(logObject.data);
                }
            }
            else {
                alert("Select one row of 'Project logs table'");
            }    
        }
    });

}
