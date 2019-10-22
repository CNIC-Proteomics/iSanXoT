/*
  Global variables
*/
let exceptor = require('./exceptor');
let sessioner = require('./sessioner');
const { ipcRenderer } = require('electron');
let psTree = require(process.env.ISANXOT_NODE_PATH + '/ps-tree');
let fs = require('fs');
let path = require('path');
let resizeId = null;

/* Firing resize event only when resizing is finished */
function doneResizing() {
    // resize table from the window size
    let winwidth = $(window).width();
    let winheight = $(window).height();
    if ( $('#hot').length ) {
        let newheight = winheight - 178;
        $('#hot').handsontable('updateSettings',{height: newheight});
    }
    if ( $('#hot_processes').length ) {
        let newheight = winheight - 92;
        $('#hot_processes').handsontable('updateSettings',{height: newheight});
    }
}
$(window).resize(function() {
    clearTimeout(resizeId);
    resizeId = setTimeout(doneResizing, 250);
});

window.onload = function(e) {
    // stop loading workflow
    exceptor.stopLoadingWorkflow();
    // extract the session info    
    let pids = JSON.parse( window.sessionStorage.getItem("pids") );
    let logs = JSON.parse( window.sessionStorage.getItem("logs") );
    let wfs = JSON.parse( window.sessionStorage.getItem("wfs") );
    // refresh the ids of child process from the pids
    if ( pids !== null && logs !== null && pids.length == logs.length ) {
        let c_pids = [];
        for (var i = 0; i < pids.length; i++) { 
            let pid = parseInt(pids[i]);
            let log = logs[i];
            console.log("pstree: "+pid);
            psTree(pid, function (err, children) {
                let c_pid = [];
                children.forEach(function (p) {
                    c_pid.push(p.PID);
                });
                c_pids.push(c_pid);
                // save session info
                window.sessionStorage.setItem("c_pids", JSON.stringify(c_pids));
                // send the processes structure to to main js
                if ( pids !== null && pids !== undefined ) {
                    ipcRenderer.send('send-pids', {
                        'pids': pids,
                        'c_pids': c_pids,
                        'logs': logs
                    });    
                }
            });            
        }
    }
    // resize table from the window size
    doneResizing();
    // refresh log panel
    refreshLogger();
};

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
        //     'name': 'string',
        //     'status': 'integer',
        //     'file': 'file',
        //     }]
        // init log structure
        // get the list of pids and files
        this.data = logs;
        this.files = this.data.map(a => a.file);
        this.pids = this.data.map(a => a.pid);

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
                colHeaders: ['Selected', 'PID', 'Workflow', 'Status', '%', 'Start time', 'End time', 'Path'],
                columns: [{            
                    data: 'selected',
                    type: 'checkbox',
                    className: "htCenter",
                },{
                    data: 'pid',
                    readOnly: true,
                    className: "htCenter",
                },{
                    data: 'name',
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
                height: 590,
                licenseKey: 'non-commercial-and-evaluation'
            });
        });
    }    
};


function refreshLogger() {
    // extract the session info
    let pids = JSON.parse( window.sessionStorage.getItem("pids") );
    let logs = JSON.parse( window.sessionStorage.getItem("logs") );
    let wfs  = JSON.parse( window.sessionStorage.getItem("wfs") );
    let status = 1; // init the status
    // refresh the ids of child process from the pids
    let logpanel = [];
    if ( pids !== null && logs !== null && pids.length == logs.length ) {
        for (var i = 0; i < pids.length; i++) {
            let pid = parseInt(pids[i]);
            let file = logs[i];
            let name  = wfs[i];
            logpanel.push({
                'pid': pid,
                'name': name,
                'status': status,
                'file': file,
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
        let logdata  = logtable.getData();
        for (var i = 0; i < logdata.length; i += 1) {
          let ldata = logdata[i];
          if ( ldata[0] ) {
                let pid = ldata[1];
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
            }
        }
    });
}



// var sourceDataObject = [
//     {
//     pid: 77,
//       workflow: 'Best Rock Performance',
//       selected: null,
//       method: null,
//       stime: null,
//       __children: [
//         {
//           method: 'Don\'t Wanna Fight',
//           artist: 'Alabama Shakes',
//           stime: 'ATO Records'
//         }, {
//           method: 'What Kind Of Man',
//           artist: 'Florence & The Machine',
//           stime: 'Republic'
//         }, {
//           method: 'Something From Nothing',
//           artist: 'Foo Fighters',
//           stime: 'RCA Records'
//         }, {
//           method: 'Ex\'s & Oh\'s',
//           artist: 'Elle King',
//           stime: 'RCA Records'
//         }, {
//           method: 'Moaning Lisa Smile',
//           artist: 'Wolf Alice',
//           stime: 'RCA Records/Dirty Hit'
//         }
//       ]
//     },{
//         pid: 88,
//         workflow: 'Best Metal Performance',
//       __children: [
//         {
//           method: 'Cirice',
//           artist: 'Ghost',
//           stime: 'Loma Vista Recordings'
//         }, {
//           method: 'Identity',
//           artist: 'August Burns Red',
//           stime: 'Fearless Records'
//         }, {
//           method: '512',
//           artist: 'Lamb Of God',
//           stime: 'Epic Records'
//         }, {
//           method: 'Thank You',
//           artist: 'Sevendust',
//           stime: '7Bros Records'
//         }, {
//           method: 'Custer',
//           artist: 'Slipknot',
//           stime: 'Roadrunner Records'
//         }
//     ]
// }];

// if ( $('#hot_processes').length ) {
//     let container = $('#hot_processes').handsontable({
//         data: sourceDataObject,
//         rowHeaders: true,
//         colHeaders: ['Selected', 'PID', 'Workflow', 'Method', 'Start time', 'End time'],
//         columns: [{            
//             data: 'selected',
//             type: 'checkbox'
//         },{
//             data: 'pid'
//         },{
//             data: 'workflow'
//         },{
//             data: 'method'
//         },{
//             data: 'stime'
//         },{
//             data: 'etime'
//         }],
//         nestedRows: true,
//         contextMenu: true,
//         width: '100%',
//         height: 590,      
//         licenseKey: 'non-commercial-and-evaluation'
//         });        
// }

