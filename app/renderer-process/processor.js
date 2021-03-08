/*
  Global variables
*/
let importer = require('./imports');
let exceptor = require('./exceptor');
let sessioner = require('./sessioner');
const { ipcRenderer } = require('electron');
let psTree = require(`${process.env.ISANXOT_LIB_HOME}/node/node_modules/ps-tree`);
let fs = require('fs');
let path = require('path');
let logObject = undefined;
const { dialog } = require('electron').remote


window.onload = function(e) {
    // stop loading workflow
    exceptor.stopLoadingWorkflow();

    // send the new Child Process to IPC Render and save into Session calling callback function
    sendChildProcesses();

    // extract the session info
    let pids = JSON.parse( window.sessionStorage.getItem("pids") );
    let status = 1; // init the status
    // refresh the ids of child process from the pids
    let ldata = [];
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

    // create logger object
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


/* LOGGER SECTION */

// make Promise version of fs.readFile()
fs.readFileAsync = function(filename, enc) {
    return new Promise(function(resolve, reject) {
        fs.readFile(filename, enc, function(err, data){
            if (err) 
                reject(err); 
            else
                resolve(data);
        });
    });
};

class logger {
    constructor(logs) {
        // accepts the init structure
        //     [{
        //     'pid': 'integer',
        //     'c_pids': 'list of intergers',
        //     'name': 'string',
        //     'status': 'integer',
        //     'cfgfile': 'file',
        //     'logfile': 'file',        
        //     }]
        // init log structure
        // get the list of pids and files
        this.data = logs;
        // reassign 'this' class for the following functions
        let that = this;
        // read all the files using Promise.all to time when all async readFiles has completed.
        Promise.all(this.data.map(a => this._getFile(a.cfgfile))).then(function(conts) {
            // go throught the list of PIDs objects
            let pids = that.data.map(a => a.pid);            
            for (var i = 0; i < pids.length; i++) {
                // extract the config structure for each project
                let cfg = jsyaml.load(conts[i]);
                let cfg_cmds = cfg['commands'];
                let cmds = [];
                // get the list of commands and the execution label
                for (var j = 0; j < cfg_cmds.length; j++) {
                    let c = cfg_cmds[j].map(a => ({
                        command: a.name,
                        execution_label: 'exec',
                        status: 'waiting',
                        perc: '0%',
                        stime: '-',
                        etime: '-'
        
                    }));
                    cmds.push(c);
                }
                // convert list of lists to list
                if (cmds) {
                    cmds = cmds.flat();
                }
                that.data[i].cmds = cmds;
            }
            that.createProjectLogsTable();
        });

    }
    // utility function, return Promise
    _getFile(filename) {
        return fs.readFileAsync(filename, 'utf8');
    }
    _parseDate(date) {
        let d  = new Date( date.toString().replace(/\[|\]/g,'') );
        let d2 = `${d.getFullYear()}-${(d.getMonth()+1)}-${d.getDate()} ${d.getHours()}:${d.getMinutes()}:${d.getSeconds()}`;
        return d2;
    }
    // parse the log file
    updateLogDataFromLogFile(data, cont) {
        // don't update date if project has been stopped
        if ( data.status == 'stopped' ) return 
        // get the log content
        let lines = cont.match(/(.*)/mg);
        // remove empty values
        lines = lines.filter(function (el) {
            return (el != null) && (el != '');
        });
        // get log variables for the root process
        if ( lines.length >= 1 ) { data.status = 'preparing' }
        data.perc   = '0%';
        data.message    = '';
        data.stime  = '-';
        data.etime  = '-';
        data.path  = path.dirname(data.logfile);
        // get log variables for the sub-processes
        let num_cmds = 0;
        let total_cmds = 0;
        for (var i = 0; i < lines.length; i++) {
            let line = lines[i];
            if ( line != "" ) {
                // parse log file for the project table ----
                // parse the error messages
                if (line.startsWith('ERROR')) {
                    data.status = 'error';
                    data.perc = '-';
                    data.message = `${lines.slice(i+1).join('\n')}`;
                }
                // save the intermediante steps
                else if (line.startsWith('MYSNAKE_LOG_PREPARING')) {
                    let l = line.split('\t');
                    let time = l[1];
                    data.status = 'preparing';
                    data.stime = this._parseDate(time)
                }
                else if (line.startsWith('MYSNAKE_LOG_VALIDATING')) {
                    data.status = 'validating';
                }
                else if (line.startsWith('MYSNAKE_LOG_STARTING')) {
                    data.status = 'starting';
                }
                // parse for the project log table
                else if (line.startsWith('MYSNAKE_LOG_EXECUTING')) {
                    let l = line.split('\t');
                    total_cmds = l[2];
                    data.status = 'running';
                }
                else if (line.startsWith('MYSNAKE_LOG_FINISHED')) {
                    let l = line.split('\t');
                    let time = l[1];
                    data.status = 'finished';
                    data.perc   = '100%';
                    data.etime = this._parseDate(time)
                }
                // parse log file for the workflow table (commands) ----
                // parse the start log
                else if (line.startsWith('MYSNAKE_LOG_START_RULE_EXEC')) {
                    let l = line.split('\t');
                    let time = l[1];
                    let cmd = l[2];
                    let cmd_exec = l[3];
                    let rule_name = l[4];
                    let rule_perc = l[5];
                    // get the index from the name
                    let cmd_index = importer.getIndexParamsWithAttr(data.cmds, 'command', cmd);
                    // update data
                    let perc = eval(rule_perc).toFixed(2)*100+'%';
                    data.cmds[cmd_index].status = 'running';
                    data.cmds[cmd_index].stime = time;
                    data.cmds[cmd_index].perc = perc;
                }
                else if (line.startsWith('MYSNAKE_LOG_END_RULE_EXEC')) {
                    let l = line.split('\t');
                    let time = l[1];
                    let cmd = l[2];
                    let cmd_exec = l[3];
                    let rule_name = l[4];
                    let rule_perc = l[5];
                    let status = l[6];
                    // get the index from the name
                    let cmd_index = importer.getIndexParamsWithAttr(data.cmds, 'command', cmd);
                    // update data
                    let perc = eval(rule_perc).toFixed(2)*100+'%';
                    if ( perc == '100%' ) {
                        data.cmds[cmd_index].status = 'finished';
                        data.cmds[cmd_index].etime = time;
                        data.cmds[cmd_index].perc = perc;
                    }
                    else {
                        data.cmds[cmd_index].perc = perc;
                    }
                    if ( status == 'error' ) {
                        data.cmds[cmd_index].status = status;
                    }
                    else {
                        data.cmds[cmd_index].status = 'running';
                    }
                }
                else if (line.startsWith('MYSNAKE_LOG_END_CMD_EXEC')) {
                    let l = line.split('\t');
                    let time = l[1];
                    let cmd = l[2];
                    let cmd_exec = l[3];
                    let rule_name = l[4];
                    let rule_perc = l[5];
                    let status = l[6];
                    // get the index from the name
                    let cmd_index = importer.getIndexParamsWithAttr(data.cmds, 'command', cmd);
                    // update data only when all processes of command have already finished (100%)
                    let perc = eval(rule_perc).toFixed(2)*100+'%';
                    if ( perc == '100%' ) {
                        // update cached data
                        if ( status == 'cached' ) {
                            data.cmds[cmd_index].status = status;
                            data.cmds[cmd_index].stime = time;
                            data.cmds[cmd_index].etime = time;
                            data.cmds[cmd_index].perc = perc;
                        }
                        else if ( status == 'error' ) {
                            data.cmds[cmd_index].status = status;
                            data.cmds[cmd_index].perc = '-';
                        }
                        else {
                            data.cmds[cmd_index].status = 'finished';
                            data.cmds[cmd_index].perc = perc;
                        }
                        // calculate the percentage for the statistic of project log table
                        num_cmds += 1;
                        let proj_perc = ((num_cmds/total_cmds)*100).toFixed(2)+'%';
                        data.perc = proj_perc    
                    }
                }

            }
        }
    }

    // create project logs table
    createProjectLogsTable() {
        // reassign 'this' class for the following functions
        let that = this;
        // read all the files using Promise.all to time when all async readFiles has completed.
        Promise.all(this.data.map(a => this._getFile(a.logfile))).then(function(conts) {
            let pids = that.data.map(a => a.pid);
            // read athe log file and update the log data
            for (var i = 0; i < pids.length; i++) {
                that.updateLogDataFromLogFile(that.data[i], conts[i]);
            }
            // create log table
            $(`#projectlogs .logtable`).handsontable({
                data: that.data,
                colHeaders: ['PID', 'Status', '%', 'Start time', 'End time', 'Path', 'Message', 'Cmds'],
                currentRowClassName: 'currentRow',
                selectionMode: 'single',
                rowHeaders: false,
                outsideClickDeselects: false,
                afterSelection: function(r,c) {
                    // create the commands logs for the selected project
                    let data = this.getDataAtRow(r);
                    that.createWorkflowLogsTable(data);
                },
                columns: [{            
                    data: 'pid',
                    readOnly: true,
                    className: "htCenter",
                },{
                    data: 'status',
                    readOnly: true,
                    className: "htCenter",
                },{
                    data: 'perc',
                    readOnly: true,
                    className: "htCenter",
                },{
                    data: 'stime',
                    readOnly: true,
                    className: "htCenter",
                },{
                    data: 'etime',
                    readOnly: true,
                    className: "htCenter",
                },{
                    data: 'path',
                    readOnly: true,
                },{
                    data: 'message',
                    readOnly: true,
                },{
                    data: 'cmds',
                    readOnly: true,
                }],
                hiddenColumns: {
                    columns: [6,7],
                    indicators: false
                },
                width: '100%',
                height: 'auto',
                licenseKey: 'non-commercial-and-evaluation'
            });
        });
    }

    // create workflow logs table
    createWorkflowLogsTable(logData) {
        // get values
        let status = logData[1] || logData['status'];
        let message = logData[6] || logData['message'];
        let cmds = logData[7] || logData['cmds'];
        // init panels
        $(`#workflowlogs .message`).html(``);
        $(`#workflowlogs .table`).html(`<div name="hot" class="logtable hot handsontable htRowHeaders htColumnHeaders"></div>`);
        // check if project has an error
        if ( status == 'error' ) {
            // remove old message/table
            $(`#workflowlogs .logtable`).html(``);
            // add the new log message
            message = message.replace(/(?:\r\n|\r|\n)/g, '<br/>');
            $(`#workflowlogs .message`).html(`<div class="alert alert-danger" role="alert"><strong>${status.toUpperCase()}</strong><br/>${message}</div>`);
        // otherwise, it prints the logs of commands
        } else {
            $(`#workflowlogs .logtable`).handsontable({
                data: cmds,
                colHeaders: ['Command', 'Exec', 'Status', '%', 'Start time', 'End time'],
                disableVisualSelection: true,
                columns: [{
                    data: 'command',
                    readOnly: true,
                    className: "htCenter",
                },{
                    data: 'execution_label',
                    readOnly: true,
                    className: "htCenter",
                },{
                    data: 'status',
                    readOnly: true,
                    className: "htCenter",
                },{
                    data: 'perc',
                    readOnly: true,
                    className: "htCenter",
                },{
                    data: 'stime',
                    readOnly: true,
                    className: "htCenter",
                },{
                    data: 'etime',
                    readOnly: true,
                    className: "htCenter",
                }],
                hiddenColumns: {
                    columns: [1],
                    indicators: false
                },
                width: '100%',
                height: 'auto',
                licenseKey: 'non-commercial-and-evaluation'
            });
            importer.doneResizing();
            $(`#projectlogs .logtable`).handsontable('render');
            // $(`#workflowlogs .logtable`).handsontable('render');
        }
    }
   
    // render log tables
    renderLogTables(data) {
        // update log tables (if apply)
        let wktable = $("#workflowlogs .logtable").data('handsontable');
        if ( wktable !== undefined ) {
            if ( data !== undefined && 'cmds' in data ) {
                $(`#workflowlogs .logtable`).handsontable({ data: data.cmds });
                $(`#workflowlogs .logtable`).handsontable('render');    
            }
        }
        let prjtable = $("#projectlogs .logtable").data('handsontable');
        if ( prjtable !== undefined ) {
            if ( data !== undefined ) {
                $(`#projectlogs .logtable`).handsontable({ data: data });
                $(`#projectlogs .logtable`).handsontable('render');
            }
        }
    }

};

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
    }

    // refresh log panel
    setTimeout(refreshLogger, 10000);
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
