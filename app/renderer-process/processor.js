/*
  Global variables
*/
const { ipcRenderer } = require('electron');
let cProcess = require('child_process');
let psTree = require(process.env.ISANXOT_NODE_PATH + '/ps-tree');
let proc = null;
let resizeId = null;
let path = require('path');
let importer = require('./imports');
let exceptor = require('./exceptor');
let logger = require('./logger');

/* Firing resize event only when resizing is finished */
function doneResizing() {
    // by default:
    // width: 1600,
    // height: 850,
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

function createLogPanel(logpanel) {
    let logdata = [];
    if ( $('#hot_processes').length ) {
        for (var i = 0; i < logpanel.length; i++) {
            let pid = logpanel[i].pid;
            let log = logpanel[i].file;
            let wf  = logpanel[i].name;
            logdata.push({
                selected: null,
                'pid': pid,
                'workflow': wf,
                'method': null,
                'stime': null,
                'etime': null,
                'path': log,
                __children: []
            });
        }
        $('#hot_processes').handsontable({
            data: logdata,
            colHeaders: ['Selected', 'PID', 'Workflow', 'Methods', 'Start time', 'End time', 'Path'],
            columns: [{            
                data: 'selected',
                type: 'checkbox'
            },{
                data: 'pid'
            },{
                data: 'workflow'
            },{
                data: 'method'
            },{
                data: 'stime'
            },{
                data: 'etime'
            },{
                data: 'path'
            }],
            rowHeaders: true,
            nestedRows: true,
            width: '100%',
            height: 590,
            licenseKey: 'non-commercial-and-evaluation'
        });    
    }
}

function refreshLogger() {
    let logpanel = [];
    // extract the session info
    let pids = JSON.parse( window.sessionStorage.getItem("pids") );
    let logs = JSON.parse( window.sessionStorage.getItem("logs") );
    let wfs  = JSON.parse( window.sessionStorage.getItem("wfs") );

    // refresh the ids of child process from the pids
    if ( pids !== null && logs !== null && pids.length == logs.length ) {
        for (var i = 0; i < pids.length; i++) {
            let pid = parseInt(pids[i]);
            let log = logs[i];
            let wf  = wfs[i];
            let l = new logger.log(pid, log, wf);
            logpanel.push(l);
        }
    }

    // create Panel
    createLogPanel(logpanel);
}

/* SESSION SECTION */

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
function addProcessesToSession(pid, log, cfg) {
    // get the name of workflow
    let wfname = path.basename(cfg, '.json');

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
                ipcRenderer.send('load-page', `${__dirname}/../processes.html`);
                break;
            }
        }
    });
};

/* EXECUTION SECTION */

// Exec process
function execProcess(cmd, log, cfg) {
    // eexecute command line
    proc = cProcess.exec(cmd);

    // save the process id in the session storage
    addProcessesToSession(proc.pid, log, cfg);

    // Handle on stderr
    proc.stderr.on('data', (data) => {
      console.log(`stderr: ${data}`);
      exceptor.showMessageBox('Error Message', `${data}`);
    });
  
    // Handle on exit event
    proc.on('close', (code) => {
        var preText = `Child exited with code ${code} : `;
        console.info(preText);
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
        let cmd_smk    = `"${process.env.ISANXOT_PYTHON3x_HOME}/tools/Scripts/snakemake.exe" --configfile "${params.cfgfile}" --snakefile "${smkfile}" --cores ${params.nthreads} --directory "${params.outdir}" --rerun-incomplete`;
        let cmd_unlock = `${cmd_smk} --unlock `;
        let cmd_clean  = `${cmd_smk}  --cleanup-metadata "${smkfile}"`;
        // Sync process that Unlock the output directory
        // First we unlock the ouput directory
        let cmd1 = `${cmd_unlock} && ${cmd_clean}`
        console.log(cmd1);
        cProcess.execSync(cmd1);
        // Then, we execute the workflow
        let cmd2 = `${cmd_smk} > "${params.logfile}" 2>&1`;
        console.log(cmd2);
        execProcess(cmd2, params.logfile, cfgfile);
      }
    });
}

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
