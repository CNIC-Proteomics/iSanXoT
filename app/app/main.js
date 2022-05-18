/*
 * Import libraries and create Variables
 */

// Modules to control application life and create native browser window
const { app, Menu, BrowserWindow, ipcMain, dialog } = require('electron');
const fs = require('fs');
const path = require("path");
const url = require('url');

// Keep a global reference of the window object, if you don't, the window will
// be closed automatically when the JavaScript object is garbage collected.
let mainWindow;

// Keep a global varible for the installation
let installation = undefined;

// Variables with the processes IDs
let all_pids = { 'pids':[], 'c_pids':[] };

// Menu
let template = [
  { label: "Project", submenu: [    
    { id: 'new-project',  label: 'New Project...', accelerator: 'Ctrl+N', click() { mainWindow.webContents.send('newProject') } },
    { id: 'open-project', label: 'Open Project...', accelerator: 'Ctrl+O', click() { mainWindow.webContents.send('openProject') } },
    { id: 'save-project', label: 'Save Project', accelerator: 'Ctrl+S', enabled: false, click() { mainWindow.webContents.send('saveProject') } },
    { type: 'separator' },
    { id: 'import-workflow', label: 'Import Workflow...', enabled: false, click() { mainWindow.webContents.send('importWorkflow') } },
    { id: 'export-workflow', label: 'Export Workflow As...', enabled: false, click() { mainWindow.webContents.send('exportWorkflow') } },
    { type: 'separator' },
    { id: 'exit', label: 'Exit', accelerator: 'Shift+Ctrl+Q', click() { mainWindow.close() } }
  ]},
  { id: "processes", label: "Processes", submenu: [
    { id: "processes-main", label: 'Main page', enabled: false, click() { mainWindow.loadFile(path.join(__dirname, 'processes.html')) } }
  ]},
  { label: "Help", submenu: [
    { id: 'help_intro', label: 'Introduction', click() { mainWindow.webContents.send('openHelper', '_Introduction') } },
    { id: 'get_started', label: 'Get Started', click() { mainWindow.webContents.send('openHelper', '_Get_Started') } },
    { label: 'Modules', submenu: [
      { id: 'help_cmd-rel-creator', label: 'RELS CREATOR', click() { mainWindow.webContents.send('openHelper', '_RELS_CREATOR') } },
      { id: 'help_cmd-level-creator', label: 'LEVEL CREATOR', click() { mainWindow.webContents.send('openHelper', '_LEVEL_CREATOR') } },
      { id: 'help_cmd-level-calibrator', label: 'LEVEL CALIBRATOR', click() { mainWindow.webContents.send('openHelper', '_LEVEL_CALIBRATOR') } },
      { id: 'help_cmd-integrate', label: 'INTEGRATE', click() { mainWindow.webContents.send('openHelper', '_INTEGRATE') } },
      { id: 'help_cmd-norcombine', label: 'NORCOMBINE', click() { mainWindow.webContents.send('openHelper', '_NORCOMBINE') } },
      { id: 'help_cmd-ratios', label: 'RATIOS', click() { mainWindow.webContents.send('openHelper', '_RATIOS') } },
      { id: 'help_cmd-sbt', label: 'SBT', click() { mainWindow.webContents.send('openHelper', '_SBT') } },
      { id: 'help_cmd-report', label: 'REPORT', click() { mainWindow.webContents.send('openHelper', '_REPORT') } },
      { id: 'help_cmd-sanson', label: 'SANSON', click() { mainWindow.webContents.send('openHelper', '_SANSON') } },
      { id: 'help_cmd-wspp-sbt', label: 'WSPP-SBT', click() { mainWindow.webContents.send('openHelper', '_WSPP-SBT') } },
      { id: 'help_cmd-wsppG-sbt', label: 'WSPPG-SBT', click() { mainWindow.webContents.send('openHelper', '_WSPPG-SBT') } },
      { id: 'help_cmd-wpp-sbt', label: 'WPP-SBT', click() { mainWindow.webContents.send('openHelper', '_WPP-SBT') } },
      { id: 'help_cmd-wppG-sbt', label: 'WPPG-SBT', click() { mainWindow.webContents.send('openHelper', '_WPPG-SBT') } }
    ]},
    { id: 'input_adaptor', label: 'Input Adaptor', click() { mainWindow.webContents.send('openHelper', '_Adaptors') } },
    { id: 'special_params', label: 'Special Parameters', click() { mainWindow.webContents.send('openHelper', '_Special_parameters') } },
    { id: 'license', label: 'License', click() { mainWindow.webContents.send('openHelper', '_License') } }
  ]},
]

// Add 'debugging' menu
if (process.env.ISANXOT_MODE == "debug") {
  template.push({ label: "Debug", submenu: [
    { label: 'Reload', accelerator: 'Ctrl+R', click() { mainWindow.reload() } },
    { label: 'Toggle Developer Tools', accelerator: 'Ctrl+D', click() { mainWindow.webContents.openDevTools() } }
  ]});
}
// create menu
const menu = Menu.buildFromTemplate(template)

/*
 * Local functions
*/

// Create the main Window
function createMainWindow () {
  // create the browser window.
  mainWindow = new BrowserWindow({
    minWidth: 1250,
    minHeight: 850,
    width: 1250,
    height: 850,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
      enableRemoteModule: true
    },
    // resizable: false,
    'icon': path.join(__dirname, 'assets/images/isanxot.png')
  });

  // Set application menu
  Menu.setApplicationMenu(menu);

  // debug mode
  if (process.env.ISANXOT_MODE == "debug") {
    mainWindow.webContents.openDevTools();
  }
  else { // remove console log in production mode
    console.log = function() {};
  }

  // maximum size
  // mainWindow.maximize();

  // give the focus
  mainWindow.focus();

  // Emitted when the window is starting to be close.
  mainWindow.on('close', function(event) {
    console.log("** close windows");
    let choice = reallyWantToClose();
    console.log("   event prevent");
    if (choice === 1) event.preventDefault();
  });

  // load the main html
  mainWindow.loadFile(path.join(__dirname, 'index.html'));

}; // end createMainWindow

// Prevent the close of app
function reallyWantToClose() {
  let opts = {      
    type: 'question',
    buttons: ['Yes', 'No'],
    title: 'Confirm',
    message: 'Do you really want to close the application?'
  };
  let choice = dialog.showMessageBoxSync(mainWindow, opts);
  return choice;
};

// Kill processes
// start first with the child processes (at the end of array)
function KillProcceses(all_pids) {
  console.log(`   kill child processes: ${all_pids['c_pids']}`);
  all_pids['c_pids'].reverse().forEach(function(pid) {
    try {
      console.log(`${pid} has been killed!`);
      process.kill(pid);
    }
    catch (e) {
      console.log(`error killing ${pid}: ${e}`);
    }
  });
  console.log(`   kill processes: ${all_pids['pids']}`);
  all_pids['pids'].forEach(function(pids) {
    let log = pids[0];
    pids.slice(1).reverse().forEach(function(pid) {
      try {
        console.log(`${pid} has been killed!`);
        process.kill(pid);
      }
      catch (e) {
        console.log(`error killing ${pid}: ${e}`);
      }
    });  
  });
};

// Create frameless window
const framelessWindow = () => {
  const mainWindow = new BrowserWindow({
      width: 700,
      height: 460,
      resizable: false,
      transparent: true,
      frame: false,
      webPreferences: {
          nodeIntegration: true,
          contextIsolation: false,
          enableRemoteModule: true
      },
      'icon': path.join(__dirname, 'assets/images/isanxot.png')
  });

  // give the focus
  mainWindow.focus()

  // debug mode
  if (process.env.ISANXOT_MODE == "debug") {
    mainWindow.webContents.openDevTools();
  }

  // Emitted when the window is starting to be close.
  mainWindow.on('close', function() {
    console.log("** close frameless");
    for (var i in installation) console.log(`${i}=${installation[i]}`);
    if (installation !== undefined) {
      if (installation.code === 0) createMainWindow();
    }
  });

  // load the main html
  mainWindow.loadFile(path.join(__dirname, "frameless.html"));
  
}; // end framelessWindow


/*
App functions
*/

// This method will be called when Electron has finished initialization 
// and is ready to create browser windows.
// Some APIs can only be used after this event occurs.
// app.on('ready', createMainWindow);
app.on('ready', function () {
  console.log("** ready");
  framelessWindow();
});

app.on('activate', function () {
  console.log("** activate");
  // On OS X it's common to re-create a window in the app when the
  // dock icon is clicked and there are no other windows open.
  if (mainWindow === null) {
    createMainWindow();
  }
});

// before quit: App close handler
app.on('before-quit', function (event) {
  console.log("** before-quit");
  console.log("   remove all listeners");
  mainWindow.removeAllListeners('close');
  mainWindow.close();  
});

// When all windows are closed...
app.on('window-all-closed', function () {
  console.log("** window-all-closed");
  // kill all processes
  console.log("   kill all processes");
  KillProcceses(all_pids);
  console.log("   app quit");
  // if (process.platform !== "darwin") {
    app.quit();
  // }
});


// ---------------

// In this file you can include the rest of your app's specific main process
// code. You can also put them in separate files and require them here.

// Get the result of installation
ipcMain.on('log', function(event, arg) {
  console.log(arg);
});

// Get the result of installation
ipcMain.on('get-install', function(event, arg) {
  installation = arg;
});

// Get the result of installation
ipcMain.on('send-env', function(event, arg) {
  // update values
  for (var key in arg) {
    // env[key] = arg[key];
    console.log(`${key}=${arg[key]}`);
    process.env[key] = arg[key];
  }
});

// Load the new URL
ipcMain.on('load-page', function(event, arg) {
  mainWindow.loadURL(
    url.format({
        protocol: 'file',
        slashes: true,
        pathname: arg,
    })
  ).catch( (error) => {
          console.log(error);
  });
});

// Get the PIDs
ipcMain.on('send-pids', function(event, arg) {
  console.log('receive pids');
  console.log(arg);
  all_pids['pids'] = arg['pids'];
});  

// Get the Child PID
ipcMain.on('send-cpid', function(event, arg) {
  console.log('receive child pid');
  console.log(arg);
  // add unique ids
  if (all_pids['c_pids'].indexOf(arg['cpid']) === -1) {
    all_pids['c_pids'].push(arg['cpid']);
  }
});  
