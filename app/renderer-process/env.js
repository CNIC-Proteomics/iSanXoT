/*
 * Import libraries
 */

let fs = require('fs');
let path = require('path');
let cProcess = require('child_process');
const { ipcRenderer, remote } = require('electron');
const { BrowserWindow } = require('electron').remote;
const mainWindow = BrowserWindow.getFocusedWindow();


let exceptor = require('./exceptor');

// window for trace logs
var win = null;
var trace_log = ''; // keep the logs

/*
 * Local functions
 */
function printInDetail(data) {
    trace_log += data; // save the trace logs
    if ( win !== null ) {
        // render: send log trace
        ipcRenderer.send('installation-detail', { log: data });
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
        // Handle on stderr
        proc.stderr.on('data', (data) => {
            console.log(`stderr: ${data}`);
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
                ipcRenderer.send('get-install', {'code': code, 'msg': `Close: Child exited with code ${code}: the installation was executed succesfully`});
                if (close) closeWindow();
                if (callback) callback();
            }
            else {
                ipcRenderer.send('get-install', {'code': code, 'msg':  `Close: Child exited with code ${code}: the installation was not complete`});
                exceptor.showErrorMessageBox(`${script}`, `Error ${script}`, end=false, page=false, callback=function(){closeWindow()} );
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
$('#frameless-desc-title').text('Preparing environment variables');
printInDetail('** Preparing environment variables...\n');

process.env.ISANXOT_RESOURCES = process.resourcesPath;
if (process.env.ISANXOT_MODE == "debug") { // in the case of debugging
    process.env.ISANXOT_RESOURCES = path.join(process.cwd(), 'resources');
}


// Set the python executable depending on the platform and mode
if (navigator.platform === "Win32") {
    process.env.ISANXOT_PYTHON_HOME = path.join(process.env.ISANXOT_RESOURCES, 'exec/python-win-x64');
    process.env.ISANXOT_PYTHON_EXEC = path.join(process.env.ISANXOT_PYTHON_HOME, 'python.exe');
    requirements = path.join(process.env.ISANXOT_RESOURCES, 'env/requirements_backend_win-x64.txt');
}
else if (navigator.platform === "MacIntel") {
    process.env.ISANXOT_PYTHON_HOME = path.join(process.env.ISANXOT_RESOURCES, 'exec/python-darwin-x64');
    process.env.ISANXOT_PYTHON_EXEC = path.join(process.env.ISANXOT_PYTHON_HOME, 'bin/python3');
    requirements = path.join(process.env.ISANXOT_RESOURCES, 'env/requirements_backend_darwin-x64.txt');
}
else if (navigator.platform === "Linux x86_64") {
    process.env.ISANXOT_PYTHON_HOME = path.join(process.env.ISANXOT_RESOURCES, 'exec/python-linux-x64');
    process.env.ISANXOT_PYTHON_EXEC = path.join(process.env.ISANXOT_PYTHON_HOME, 'bin/python3');
    requirements = path.join(process.env.ISANXOT_RESOURCES, 'env/requirements_backend_linux-x64.txt');
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


// Send environment variables
ipcRenderer.send('send-env', { 'ISANXOT_RESOURCES': process.env.ISANXOT_RESOURCES });
ipcRenderer.send('send-env', { 'ISANXOT_SRC_HOME': path.join(process.env.ISANXOT_RESOURCES, 'src') });
ipcRenderer.send('send-env', { 'ISANXOT_ADAPTOR_HOME': path.join(process.env.ISANXOT_RESOURCES, 'adaptors') });
ipcRenderer.send('send-env', { 'ISANXOT_ADAPTOR_INIT': path.join(process.env.ISANXOT_RESOURCES, 'adaptors/main_input') });
ipcRenderer.send('send-env', { 'ISANXOT_WFS_HOME': path.join(process.env.ISANXOT_RESOURCES, 'wfs') });
ipcRenderer.send('send-env', { 'ISANXOT_SAMPLES_DIR': path.join(process.env.ISANXOT_RESOURCES, 'wfs/samples') });
ipcRenderer.send('send-env', { 'ISANXOT_NODE_MODULES': path.join(process.env.ISANXOT_RESOURCES, 'node_modules') });


// Set the icon
process.env.ISANXOT_ICON = path.join(process.cwd(), 'app/assets/images/isanxot.png');
ipcRenderer.send('send-env', {'ISANXOT_ICON': process.env.ISANXOT_ICON});


// Prepare commands consecutively
let cmd1 = `"${process.env.ISANXOT_PYTHON_EXEC}" "${path.join(process.env.ISANXOT_RESOURCES, 'env/installer.py')}" "${requirements}" `; // install Python packages


// Execute the commands consecutively
$('#frameless-desc-title').text('Preparing packages');
printInDetail('** Preparing packages...\n');
execProcess('preparing packages', cmd1, close=false);



// // BEGIN: DEPRECATED BUT USEFULL: SEE HOW EXECUTE CONSECUTIVELY
// // Prepare commands consecutively
// let cmd1 = `"${python_exec}" -m venv --upgrade-deps --copies "${path.join(process.env.ISANXOT_RESOURCES, 'exec/python')}" `; // create Python environment
// let cmd2 = `"${python_exec}" "${path.join(process.env.ISANXOT_RESOURCES, 'env/installer.py')}" "${requirements}" "${path.join(process.env.ISANXOT_RESOURCES, 'exec/python')}" `; // install Python packages

// // Execute the commands consecutively
// $('#frameless-desc-title').text('Preparing Python environment');
// printInDetail('** Preparing Python environment...\n');
// execProcess('preparing python environment', cmd1, close=false,
// // Install Python packages
// // End execution
// function() {
//     $('#frameless-desc-title').text('Installing Python packages');
//     printInDetail('** Installing Python packages...\n');
//     execProcess('installing python packages', cmd2, close=true)
// });

/*
 * Events
 */
document.querySelector('#frmeless-desc-area').addEventListener('click', function() {
    win = new BrowserWindow({
        title: 'Create new project',
        width: 500,
        height: 700,
        modal: true,
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false,
            enableRemoteModule: true
        },      
        minimizable: false,
        resizable: false,
        'icon': process.env.ISANXOT_ICON,
        parent: mainWindow
    });
    win.setMenu(null);
    win.loadURL(path.join(__dirname, '../frameless-detail.html'));
    win.webContents.openDevTools();
    win.on('close', function () {
        win = null;
    });
    win.show();
    ipcRenderer.send('installation-detail', { log: trace_log });
});
