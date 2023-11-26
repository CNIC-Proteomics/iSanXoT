/*
 * Import libraries
 */

let fs = require('fs');
let path = require('path');
let cProcess = require('child_process');
const { ipcRenderer, remote } = require('electron');

let exceptor = require('./exceptor');

// N processes
var nTotalProc = 0;
var nProc = 0;

/*
 * Local functions
 */
function printInDetail(data) {
    // Increase progress bar
    if ( data.includes('** The process was completed successfully') ) {
        nProc += 1;
        let p = (nProc/nTotalProc)*100;
        if (p > 100) p = 100;
        $('.progress-bar').css('width', `${p}%`).attr('aria-valuenow', nProc);
    }
    // if ( data.startsWith('**') ) $('#frameless-desc-title').text(data.replace('** ',''));
    // if ( data.startsWith('**') ) $('#frameless-progress .progress-bar').text(data.replace('** ',''));
    // short description
    data = data.split(/\r|\n/);
    for ( let i=0; i < data.length; i++) {
        if (data[i] != '') $('#frameless-desc-short').text(data[i]);
    }
};

function getNProcesses(file) {
    try {
        let num = 0;
        let data = fs.readFileSync(file, 'utf8').toString().split('\n');
        for ( let i=0; i < data.length; i++) {
            if ( data[i] != '' && !data[i].startsWith('#') ) num += 1;
        }
        return num;
    } catch (err) {
        exceptor.showErrorMessageBox(`getNProcesses`, `Error reading the requirement file: ${file}`, end=false, page=false, callback=function(){closeWindow()} );
    }
};

function closeWindow() {
    var window = remote.getCurrentWindow();
    window.close();
};

function execProcess(script, cmd, close=false, callback) {
    try {
        // execute command line
        console.log(cmd);
        let proc = cProcess.exec(cmd);
        var procError = '';        
        // Handle on stderr
        proc.stderr.on('data', (data) => {
            console.log(`stderr: ${data}`);
            procError = data;
        });
        // Handle on stderr
        proc.stdout.on('data', (data) => {
            console.log(`stdout: ${data}`);
            printInDetail(data);
        });
        // Handle on close event
        proc.on('close', (code) => {
            console.log(`Close: Child exited with code ${code}`);
            if (code === 0) {
                printInDetail('** The installation was executed succesfully');
                ipcRenderer.send('get-install', {'code': code, 'msg': `Close: Child exited with code ${code}: the installation was executed succesfully`});
                if (close) closeWindow();
                if (callback) callback();
            }
            else {
                ipcRenderer.send('get-install', {'code': code, 'msg':  `Close: Child exited with code ${code}: the installation was not complete`});
                exceptor.showErrorMessageBox(`${script}`, `Error ${script}: ${procError}`, end=false, page=false, callback=function(){closeWindow()} );
            }
        });
        // Handle on error event
        proc.on('error', (code, signal) => {
            ipcRenderer.send('get-install', {'code': code, 'msg': `Error ${script}: Child exited with code ${code} and signal ${signal}`});
            exceptor.showErrorMessageBox(`${script}`, `Error ${script}: Child exited with code ${code} and signal ${signal}`, end=false, page=false, callback=function(){closeWindow()} );
        });
    } catch (ex) {
        ipcRenderer.send('get-install', {'code': ex.code, 'msg':  "the installation was not complete"});
        exceptor.showErrorMessageBox(`${script}`, `Error ${ex.code} \n ${ex.message}`, end=false, page=false, callback=function(){closeWindow()} );
    }
};

/*
 * Main
 */

// Set the resources folder depeding on mode
printInDetail('** Preparing environment variables...\n');

process.env.ISANXOT_RESOURCES = process.resourcesPath;
if (process.env.ISANXOT_DEV == "local") { // in the case of local debugging
    process.env.ISANXOT_RESOURCES = path.join(process.cwd(), 'resources');
}


// Set the python executable depending on the platform and mode
if (navigator.platform === "Win32") {
    process.env.ISANXOT_PYTHON_HOME = path.join(process.env.ISANXOT_RESOURCES, 'exec/python-3.9.7-win-x64');
    process.env.ISANXOT_PYTHON_EXEC = path.join(process.env.ISANXOT_PYTHON_HOME, 'python.exe');
    requirements_python = path.join(process.env.ISANXOT_RESOURCES, 'env/python/requirements_python_win-x64.txt');
    requirements_exec = path.join(process.env.ISANXOT_RESOURCES, 'env/exec/requirements_exec_win-x64.txt');
    process.env.ISANXOT_NEW_PROJECT_MODAL = true;
}
else if (navigator.platform === "MacIntel") {
    process.env.ISANXOT_PYTHON_HOME = path.join(process.env.ISANXOT_RESOURCES, 'exec/python-3.9.7-darwin-x64');
    process.env.ISANXOT_PYTHON_EXEC = path.join(process.env.ISANXOT_PYTHON_HOME, 'bin/python3');
    requirements_python = path.join(process.env.ISANXOT_RESOURCES, 'env/python/requirements_python_darwin-x64.txt');
    requirements_exec = path.join(process.env.ISANXOT_RESOURCES, 'env/exec/requirements_exec_darwin-x64.txt');
    new_project_window_modal = false; // The Modal browser in MacOSX does not work correctly
}
else if (navigator.platform === "Linux x86_64") {
    process.env.ISANXOT_PYTHON_HOME = path.join(process.env.ISANXOT_RESOURCES, 'exec/python-3.9.7-linux-x64');
    process.env.ISANXOT_PYTHON_EXEC = path.join(process.env.ISANXOT_PYTHON_HOME, 'bin/python3');
    requirements_python = path.join(process.env.ISANXOT_RESOURCES, 'env/python/requirements_python_linux-x64.txt');
    requirements_exec = path.join(process.env.ISANXOT_RESOURCES, 'env/exec/requirements_exec_linux-x64.txt');
    process.env.ISANXOT_NEW_PROJECT_MODAL = true;
}
else {
    ipcRenderer.send('get-install', {'code': 601, 'msg':  `Error setting the platform`});
    exceptor.showErrorMessageBox(`Setting the platform`, `Error setting the platform`, end=false, page=false, callback=function(){closeWindow()} );
}
if ( !fs.existsSync(process.env.ISANXOT_PYTHON_EXEC) ) {
    ipcRenderer.send('get-install', {'code': 602, 'msg':  `Error getting the python environment: ${process.env.ISANXOT_PYTHON_EXEC}`});
    exceptor.showErrorMessageBox(`Getting the python env`, `Error getting the python environment: ${process.env.ISANXOT_PYTHON_EXEC}`, end=false, page=false, callback=function(){closeWindow()} );
}
ipcRenderer.send('send-env', { 'ISANXOT_PYTHON_HOME': process.env.ISANXOT_PYTHON_HOME });
ipcRenderer.send('send-env', { 'ISANXOT_PYTHON_EXEC': process.env.ISANXOT_PYTHON_EXEC });
ipcRenderer.send('send-env', { 'ISANXOT_NEW_PROJECT_MODAL': process.env.ISANXOT_NEW_PROJECT_MODAL });


// Send environment variables
ipcRenderer.send('send-env', { 'ISANXOT_RESOURCES': process.env.ISANXOT_RESOURCES });
ipcRenderer.send('send-env', { 'ISANXOT_SRC_HOME': path.join(process.env.ISANXOT_RESOURCES, 'src') });
ipcRenderer.send('send-env', { 'ISANXOT_ADAPTOR_HOME': path.join(process.env.ISANXOT_RESOURCES, 'adaptors') });
ipcRenderer.send('send-env', { 'ISANXOT_ADAPTOR_TYPE': 'adaptor.json' });
ipcRenderer.send('send-env', { 'ISANXOT_WFS_HOME': path.join(process.env.ISANXOT_RESOURCES, 'wfs') });
ipcRenderer.send('send-env', { 'ISANXOT_SAMPLES_DIR': path.join(process.env.ISANXOT_RESOURCES, 'wfs/samples') });
ipcRenderer.send('send-env', { 'ISANXOT_NODE_MODULES': path.join(process.env.ISANXOT_RESOURCES, 'node_modules') });


// Set the icon
process.env.ISANXOT_ICON = path.join(process.cwd(), 'app/assets/images/isanxot.png');
ipcRenderer.send('send-env', {'ISANXOT_ICON': process.env.ISANXOT_ICON});


// Get the Number of Processes in Total
nTotalProc = getNProcesses(requirements_python);
nTotalProc += getNProcesses(requirements_exec);
$('.progress-bar').attr('aria-valuemax', nTotalProc);


// Prepare commands consecutively
let cmd1 = `"${process.env.ISANXOT_PYTHON_EXEC}" "${path.join(process.env.ISANXOT_RESOURCES, 'env/installer.py')}" "${requirements_python}" "${process.env.ISANXOT_PYTHON_HOME}" `; // install Python packages
let cmd2 = `"${process.env.ISANXOT_PYTHON_EXEC}" "${path.join(process.env.ISANXOT_RESOURCES, 'env/installer.py')}" "${requirements_exec}" "${path.join(process.env.ISANXOT_RESOURCES, 'exec')}" `; // install exec managers


// Execute the commands consecutively
printInDetail('** Preparing environment...\n');
execProcess('preparing environment', cmd1, close=false,
// End execution, next...
// install exec managers
function() {
    printInDetail('** Installing exec managers...\n');
    execProcess('installing exec managers', cmd2, close=true)
});
