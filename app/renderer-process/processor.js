/*
  Global variables
*/
let exceptor = require('./exceptor');
let sessioner = require('./sessioner');
const { ipcRenderer } = require('electron');
let psTree = require(`${process.env.ISANXOT_LIB_HOME}/node/node_modules/ps-tree`);
let fs = require('fs');
let path = require('path');

window.onload = function(e) {
    // stop loading workflow
    exceptor.stopLoadingWorkflow();
    // refresh log panel
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
        //     'file': 'file',
        //     }]
        // init log structure
        // get the list of pids and files
        this.data = logs;
        this.files = this.data.map(a => a.file);
        this.pids = this.data.map(a => a.pid);
        // this.c_pids = this.data.map(a => a.c_pids);
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
    parseLogText(self, i, cont) {
        // get current data log
        let data = self[i];
        // get the log content
        let blocks = cont.split(/(\n\r){1,}/g);
        // get log variables for the root process
        if ( blocks.length >= 1 ) { data.status = 'running' }
        data.selected = null;
        data.perc   = '0.1%';
        data.stime  = '-';
        data.etime  = '-';
        data.path  = path.dirname(data.file);
        // get log variables for the sub-processes
        data.__children = [];
        for (var i = 0; i < blocks.length; i++) {
            let block = blocks[i];
            if ( block.search(/^\s+$/) == -1 ) {
                let time = block.match(/\[.*?\]/g);
                if ( i == 2 && time ) { data.stime = this._parseDate(time) };
                if ( block.includes("Complete log") ) {
                    data.status = 'finished';
                    data.perc   = '100%';
                    if ( time ) { data.etime = this._parseDate(time) };
                }
                let steps = block.match(/\s*steps\s*\(.*?\)\s*done/g);
                if ( steps && steps.length > 0) {
                    let perc = steps[0].match(/\(.*?\)/g);
                    perc = perc.toString().replace(/\(|\)/g,'')
                    data.perc = perc;
                }
            }
        }
    }
    // create panel
    createLogPanel(id) {
        // read all the files using Promise.all to time when all async readFiles has completed.
        let that = this;
        let that_data = this.data;
        Promise.all(this.files.map(this._getFile)).then(function(conts) {
            for (var i = 0; i < that.pids.length; i++) {
                that.parseLogText(that_data, i, conts[i]);
            }
            // create log table
            $(`#${id}`).handsontable({
                data: that_data,
                // colHeaders: ['Selected', 'PID', 'Workflow', 'Status', '%', 'Start time', 'End time', 'Path'],
                colHeaders: ['Selected', 'PID', 'Status', '%', 'Start time', 'End time', 'Path'],
                afterSelection: function(r,c) {
                    let data = this.getDataAtRow(r);
                    let logfile = `${data[6]}/isanxot.log`;
                    let s = fs.readFileSync(logfile);
                    // remove the line with the fail due the proyect is saved in tierra
                    s = s.toString().replace(/^Failed to set marker file for job started.*/mg, '');
                    s = s.toString().replace(/^Error recording metadata for finished job.*/mg, '');
                    // add the log in the panel
                    $('#hot_processes_panel').html(s);
                    // scroll to down
                    var psconsole = $('#hot_processes_panel');
                    if (psconsole.length) {
                        psconsole.scrollTop(psconsole[0].scrollHeight - psconsole.height());
                    }
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
                }],
                rowHeaders: true,
                // nestedRows: true,
                width: '100%',
                height: 'auto',
                licenseKey: 'non-commercial-and-evaluation'
            });
        });
    }    
};

function sendChildProcesses() {
    // send the new Child Process to IPC Render and save into Session
    function sendCPIDs(list_pids) {
        // look throught the list of list of PIDs coming from the session varaible
        list_pids.forEach( function(pids, i) {
            let log = pids[0];
            let pid = pids[1];
            console.log(`get child_processes from ${pid}`);
            pids.slice(2).forEach( function(c_pid) {
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
    // extract the session info
    let pids = JSON.parse( window.sessionStorage.getItem("pids") );
    let status = 1; // init the status
    // refresh the ids of child process from the pids
    let logpanel = [];
    if ( pids !== null ) {
        for (var i = 0; i < pids.length; i++) {
            let log = pids[i][0];
            let pid = parseInt(pids[i][1]);
            let c_pids = pids[i].slice(2);
            logpanel.push({
                'pid': pid,
                'c_pids': c_pids.join(","),
                'status': status,
                'file': log,
            });
        }
    }
    // create log Panel
    let l = new logger(logpanel);
    l.createLogPanel('hot_processes');
    // refresh log panel
    setTimeout(refreshLogger, 10000);
}


/*
 * Events
 */

// Kill processes
if ( document.querySelector('#processor #stop') !== null ) {

    document.querySelector('#processor #stop').addEventListener('click', function() {

        let logtable = $("#hot_processes").data('handsontable');
        logtable.getData().forEach(function (logdata, l) {
            if ( logdata[0] ) { // check the first cell
                let pid = logdata[1];
                // get the list of all pids from the given pid (session variable)
                let session_pids = JSON.parse( window.sessionStorage.getItem("pids") );
                let pids = [];
                for (let i = 0; i < session_pids.length; i++) {
                    if ( pid == session_pids[i][1]) {
                        pids = session_pids[i].slice(1);
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
