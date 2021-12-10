/*
 * Import libraries
 */

let fs = require('fs');
let path = require('path');
let cProcess = require('child_process');
const { ipcRenderer, remote } = require('electron');

let exceptor = require('./exceptor');

/*
 * Local functions
 */
function printInDetail(data) {
    let $textarea = $('#frameless-detail > textarea');
    $('#frameless-detail > textarea').append(data);
    $textarea.scrollTop($textarea[0].scrollHeight);
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
    if (process.env.ISANXOT_MODE == "debug") {
        process.env.ISANXOT_PYTHON = path.join(process.cwd(), 'env/python-3.9.7-win-x64/python.exe');
    }
    else {
        process.env.ISANXOT_PYTHON = path.join(process.env.ISANXOT_RESOURCES, 'exec/python/python.exe');
    }
}
else if (navigator.platform === "MacIntel") {
    if (process.env.ISANXOT_MODE == "debug") {
        process.env.ISANXOT_PYTHON = path.join(process.cwd(), 'env/python-3.9.7-darwin-x64/bin/python3');
    }
    else {
        process.env.ISANXOT_PYTHON = path.join(process.env.ISANXOT_RESOURCES, 'exec/python/bin/python3');
    }
}
else if (navigator.platform === "Linux x86_64") {
    if (process.env.ISANXOT_MODE == "debug") {
        process.env.ISANXOT_PYTHON = path.join(process.cwd(), 'env/python-3.9.7-linux-x64/bin/python3');
    }
    else {
        process.env.ISANXOT_PYTHON = path.join(process.env.ISANXOT_RESOURCES, 'exec/python/bin/python3');
    }
}
else {
    ipcRenderer.send('get-install', {'code': 601, 'msg':  `Error setting the platform`});
    exceptor.showErrorMessageBox(`Setting the platform`, `Error setting the platform`, end=false, page=false, callback=function(){closeWindow()} );
}
if ( !fs.existsSync(process.env.ISANXOT_PYTHON) ) {
    ipcRenderer.send('get-install', {'code': 602, 'msg':  `Error getting the python environment: ${process.env.ISANXOT_PYTHON}`});
    exceptor.showErrorMessageBox(`Getting the python env`, `Error getting the python environment: ${process.env.ISANXOT_PYTHON}`, end=false, page=false, callback=function(){closeWindow()} );
}
ipcRenderer.send('send-env', { 'ISANXOT_PYTHON': process.env.ISANXOT_PYTHON });


// Send environment variables
ipcRenderer.send('send-env', { 'ISANXOT_RESOURCES': process.env.ISANXOT_RESOURCES });
ipcRenderer.send('send-env', { 'ISANXOT_SRC_HOME': path.join(process.env.ISANXOT_RESOURCES, 'src') });
ipcRenderer.send('send-env', { 'ISANXOT_ADAPTOR_HOME': path.join(process.env.ISANXOT_RESOURCES, 'adaptors') });
ipcRenderer.send('send-env', { 'ISANXOT_ADAPTOR_INIT': path.join(process.env.ISANXOT_RESOURCES, 'adaptors/main_input') });
ipcRenderer.send('send-env', { 'ISANXOT_WFS_HOME': path.join(process.env.ISANXOT_RESOURCES, 'wfs') });
ipcRenderer.send('send-env', { 'ISANXOT_SAMPLES_DIR': path.join(process.env.ISANXOT_RESOURCES, 'samples') });
ipcRenderer.send('send-env', { 'ISANXOT_NODE_MODULES': path.join(process.env.ISANXOT_RESOURCES, 'node_modules') });


// Set the icon
process.env.ISANXOT_ICON = path.join(process.cwd(), 'app/assets/images/isanxot.png');
ipcRenderer.send('send-env', {'ISANXOT_ICON': process.env.ISANXOT_ICON});


// Prepare commands consecutively
let requirements = path.join(process.env.ISANXOT_RESOURCES, 'exec/python/requirements.txt');
let cmd1 = `"${process.env.ISANXOT_PYTHON}" "${path.join(process.env.ISANXOT_RESOURCES, 'env/installer.py')}" "${requirements}" "${path.join(process.env.ISANXOT_RESOURCES, 'exec/python')}" `; // install Python packages


// Execute the commands consecutively
$('#frameless-desc-title').text('Preparing packages');
printInDetail('** Preparing packages...\n');
execProcess('preparing packages', cmd1, close=true);




// BEGIN: DEPRECATED BUT USEFULL: SEE HOW EXECUTE CONSECUTIVELY
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

