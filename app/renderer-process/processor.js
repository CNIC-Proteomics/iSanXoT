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
const STATUS = {
    1: 'starting',
    2: 'running',
    3: 'finished',
    4: 'error',
    5: 'stopped',
    6: 'succesdfully'
}
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
    // parse text file
    updateLogDataFromLogFile(data, cont) {
        // get the log content
        let lines = cont.match(/(.*)/mg);
        // remove empty values
        lines = lines.filter(function (el) {
            return (el != null) && (el != '');
        });
        // get log variables for the root process
        if ( lines.length >= 1 ) { data.status = 'preparing' }
        data.selected = null;
        data.perc   = '0%';
        data.stime  = '-';
        data.etime  = '-';
        data.path  = path.dirname(data.logfile);
        // get log variables for the sub-processes
        let num_cmds = 0;
        let total_cmds = 0;
        for (var i = 0; i < lines.length; i++) {
            let line = lines[i];
            if ( line != "" ) {

                // parse the error messages
                if (line.startsWith('ERROR')) {
                    exceptor.showMessageBox('error',`${lines.slice(i+1).join('\n')}`, `${line}`, true);
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

                // parse for the workflow log table (commands)
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
                    }
                    data.cmds[cmd_index].perc = perc;
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
                        // update data
                        if ( status == 'cached' ) {
                            data.cmds[cmd_index].status = status;
                            data.cmds[cmd_index].stime = time;
                            data.cmds[cmd_index].etime = time;
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
    // create project logs table
    createProjectLogsTable() {
        // reassign 'this' class for the following functions
        let that = this;
        // read all the files using Promise.all to time when all async readFiles has completed.
        Promise.all(this.data.map(a => this._getFile(a.logfile))).then(function(conts) {
            let pids = that.data.map(a => a.pid);
            for (var i = 0; i < pids.length; i++) {
                that.updateLogDataFromLogFile(that.data[i], conts[i]);
            }
            // create log table
            $(`#projectlogs .logtable`).handsontable({
                data: that.data,
                colHeaders: ['Selected', 'PID', 'Status', '%', 'Start time', 'End time', 'Path', 'Cmds'],
                currentRowClassName: 'currentRow',
                selectionMode: 'single',
                rowHeaders: false,
                outsideClickDeselects: false,
                afterSelection: function(r,c) {
                    let data = this.getDataAtRow(r);
                    let cmds = data[7];
                    that.createWorkflowLogsTable(cmds);
                },
                columns: [{            
                    data: 'selected',
                    type: 'checkbox',
                    className: "htCenter",
                },{
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
                    data: 'cmds',
                    readOnly: true,
                }],
                hiddenColumns: {
                    columns: [7],
                    indicators: false
                },
                width: '100%',
                height: 'auto',
                licenseKey: 'non-commercial-and-evaluation'
            });
        });
    }
    // create workflow logs table
    createWorkflowLogsTable(data) {
        // create log table
        $(`#workflowlogs .logtable`).handsontable({
            data: data,
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
        $(`#workflowlogs .logtable`).handsontable('render');
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

function refreshLogger() {
    // send the new Child Process to IPC Render and save into Session calling callback function
    sendChildProcesses();

    // if project has been selected, refresh the Workflow log table
    // get the data log of selected row
    let logtable = $("#projectlogs .logtable").data('handsontable');
    if (logtable !== undefined) {
        // take into account the table has the restrinction only one row/column (selectionMode: 'single')
        let selRange = logtable.getSelected();
        if ( selRange !== undefined ) {
            selRange = selRange[0];
            let r = selRange[0], c = selRange[1], r2 = selRange[2], c2 = selRange[3];
            // get the data log of selected row
            if (r == r2) {
                // get data from selected selected row (PID project)
                let selRow = logtable.getDataAtRow(r);
                let pid = selRow[1];
                let log_index = importer.getIndexParamsWithAttr(logObject.data, 'pid', pid);
                let logData = logObject.data[log_index];
                let logfile = logData.logfile;
                // get the log content
                let s = fs.readFileSync(logfile);
                let cont = s.toString();
                // update the log tables (project and workflow)
                logObject.updateLogDataFromLogFile(logData, cont);
                // render log tables
                logObject.renderLogTables()
            }
        }
        else {
            // update project log table

            // extract the session info
            let pids = JSON.parse( window.sessionStorage.getItem("pids") );
            // refresh the ids of child process from the pids
            let ldata = [];
            if ( pids !== null ) {
                for (var i = 0; i < pids.length; i++) {
                    let logfile = pids[i][1];
                    // get the log content
                    let s = fs.readFileSync(logfile);
                    let cont = s.toString();
                    // parse log file and update the data
                    logObject.updateLogDataFromLogFile(logObject.data[i], cont);
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

    document.querySelector('#processor #stop').addEventListener('click', function() {

        let logtable = $("#projectlogs .logtable").data('handsontable');
        logtable.getData().forEach(function (logdata, l) {
            if ( logdata[0] ) { // check the first cell
                let pid = logdata[1];
                // get the list of all pids from the given pid (session variable)
                let session_pids = JSON.parse( window.sessionStorage.getItem("pids") );
                let pids = [];
                for (let i = 0; i < session_pids.length; i++) {
                    if ( pid == session_pids[i][2]) {
                        pids = session_pids[i].slice(2);
                    }
                }                
                // we start from the end (reverse)
                // we get the child processes from the list of pids (session variable)
                // kill the all processes
                pids.reverse().forEach(function (pid) {
                    console.log(`Look for child processes from sms ${pid}`);
                    psTree(pid, function (err, children, callback) {  // check if it works always
                        children.forEach(function (p) {
                            try {
                                console.log(`${p.PID} sub-process from ${pid} has been killed!`);
                                process.kill(p.PID);
                            } catch (e) {
                                console.log(`error killing ${p.PID}: ${e}`);
                            }
                        });
                        // kill the main process
                        try {
                            console.log(`${pid} has been killed!`);
                            process.kill(pid);
                        } catch (e) {
                            console.log(`error killing ${pid}: ${e}`);
                        }
                    });    
                });  
            }
        });
    });
}
