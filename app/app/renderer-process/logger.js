/*
 * Import libraries
 */

let fs = require('fs');
let path = require('path');

let importer = require('./imports');
let commoner = require('./common');
const { waitForDebugger } = require('inspector');

/*
 * Local functions
 */

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

// Open Help Modals
function openHelpModal(path, prefix) {
    // get all log files that start with the command name
    let lfiles = fs.readdirSync(path).filter(fn => fn.startsWith(prefix));
    // read all the log files
    let logcont = '';
    for (let i = 0; i < lfiles.length; i++) {
        let f = `${path}/${lfiles[i]}`;
        let s = fs.readFileSync(f);
        logcont += s.toString();
        logcont += '\n------------\n';
    }
    // insert the log content into modal window
    $(`#panel-immobilizer .modal-body span`).text(logcont);
    // open modal window
    $(`#panel-immobilizer .modal`).modal();
}

/*
 * Class
 */

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
                    for (var k = 0; k < cfg_cmds[j]['cmds'].length; k++) {
                        let c = cfg_cmds[j]['cmds'][k]
                        cmds.push({
                            command: c.name,
                            execution_label: 'exec',
                            status: 'waiting',
                            perc: '0%',
                            stime: '-',
                            etime: '-'
                        });
                    }
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
        data.message    = '';
        data.stime  = '-';
        data.etime  = '-';
        data.perc   = '0%';
        for (var i = 0; i < data.cmds.length; i++) {
            data.cmds[i].stime = '-';
            data.cmds[i].etime = '-';
        }
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
                    data.status = 'wf error';
                    data.perc = '-';
                    data.message = `${lines.slice(i).join('\n')}`;
                }
                // save the intermediante steps
                else if (line.startsWith('MYSNAKE_LOG_STARTING')) {
                    let l = line.split('\t');
                    let time = l[1];
                    data.status = 'starting';
                    data.stime = this._parseDate(time);
                }
                else if (line.startsWith('MYSNAKE_LOG_PREPARING')) {
                    data.status = 'preparing';
                }
                else if (line.startsWith('MYSNAKE_LOG_VALIDATING')) {
                    data.status = 'validating';
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
                    data.etime = this._parseDate(time);
                }
                // parse log file for the workflow table (commands) ----
                // parse the start log
                else if (line.startsWith('MYSNAKE_LOG_START_RULE_EXEC')) {
                    let l = line.split('\t');
                    let time = l[1];
                    let cmd = l[2];
                    let forced_exec = l[3];
                    let rule_name = l[4];
                    let proj_perc = l[5];
                    let rule_perc = l[6];
                    let status = l[7];
                    // get the index from the name
                    let cmd_index = commoner.getIndexParamsWithAttr(data.cmds, 'command', cmd);
                    // update data: get the first values from the the first started rule
                    if ( cmd_index !== undefined ) {
                        data.cmds[cmd_index].status = 'running';
                        if ( data.cmds[cmd_index].stime == '-') data.cmds[cmd_index].stime = time;
                        data.cmds[cmd_index].path = data.path;    
                    }
                }
                else if (line.startsWith('MYSNAKE_LOG_END_RULE_EXEC')) {
                    let l = line.split('\t');
                    let time = l[1];
                    let cmd = l[2];
                    let forced_exec = l[3];
                    let rule_name = l[4];
                    let proj_perc = l[5];
                    let rule_perc = l[6];
                    let status = l[7];
                    // get the index from the name
                    let cmd_index = commoner.getIndexParamsWithAttr(data.cmds, 'command', cmd);
                    // update the data
                    if ( cmd_index !== undefined ) {
                        // get the percentage of executed rules within a command
                        let perc = eval(rule_perc).toFixed(2)*100+'%';
                        if ( status == 'error' ) { // prority the error status
                            data.cmds[cmd_index].status = status;
                            data.cmds[cmd_index].perc = '-';
                            data.cmds[cmd_index].etime = time;
                            data.status = 'cmd error'; // for the project table
                        }
                        else { // then, the rest of status
                            if ( perc == '100%' ) {
                                data.cmds[cmd_index].status = status;
                                data.cmds[cmd_index].perc = '100%';
                                data.cmds[cmd_index].etime = time; // get the last time (the last finished rule)
                            }
                            else {
                                data.cmds[cmd_index].perc = perc;
                            }
                        }
                    }
                }
                else if (line.startsWith('MYSNAKE_LOG_END_CMD_EXEC')) {
                    let l = line.split('\t');
                    let time = l[1];
                    let cmd = l[2];
                    let forced_exec = l[3];
                    let rule_name = l[4];
                    let cmd_perc = l[5];
                    let rule_perc = l[6];
                    let status = l[7];
                    // get the index from the name
                    let cmd_index = commoner.getIndexParamsWithAttr(data.cmds, 'command', cmd);
                    // update the data
                    if ( cmd_index !== undefined ) {
                        if ( status == 'error' ) { // prority the error status
                            data.cmds[cmd_index].status = status;
                            data.cmds[cmd_index].perc = '-';
                            data.cmds[cmd_index].etime = time;
                            data.status = 'cmd error'; // for the project table
                        }
                        else if ( status == 'cached' ) {
                            data.cmds[cmd_index].status = status;
                            data.cmds[cmd_index].stime = time;
                            data.cmds[cmd_index].etime = time;
                            data.cmds[cmd_index].perc = '100%';
                        }
                        // update the percentage of executed commands if incrises the value
                        cmd_perc = eval(cmd_perc).toFixed(2)*100;
                        let proj_perc = parseFloat(data.perc.replace('%',''));
                        if ( cmd_perc > proj_perc ) data.perc = cmd_perc+'%';
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
            // read the log file and update the log data
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
                    if (!commoner.allBlanks(data)) {
                        that.createWorkflowLogsTable(data);
                    }
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
        $(`#workflowlogs p`).css('display','block');
        // check if project has an error
        if ( status == 'wf error' ) {
            // remove old message/table
            $(`#workflowlogs .logtable`).html(``);
            // add the new log message
            message = message.replace(/(?:\r\n|\r|\n)/g, '<br/>');
            $(`#workflowlogs .message`).html(`<div class="alert alert-danger" role="alert"><strong>${status.toUpperCase()}</strong><br/>${message}</div>`);
        // otherwise, it prints the logs of commands
        } else {
            $(`#workflowlogs .logtable`).handsontable({
                data: cmds,
                colHeaders: ['Command', 'Exec', 'Status', '%', 'Start time', 'End time', 'Path'],
                disableVisualSelection: true,
                afterSelection: function(r,c) {
                    // open Modal window of the current command reading the logs
                    let data = this.getDataAtRow(r);
                    let path = data[6];
                    let cmd_name = data[0];
                    if ( path !== null && path !== undefined && cmd_name !== null && cmd_name !== undefined ) {
                        openHelpModal(path, cmd_name);                        
                    }
                },
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
                },{
                    data: 'path',
                    readOnly: true,
                    className: "htCenter",
                }],
                hiddenColumns: {
                    columns: [1,6],
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

}; // end class logger

module.exports = logger;