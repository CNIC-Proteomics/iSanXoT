/*
 * Import libraries and create Variables
 */

// Modules to control application life and create native browser window
const { app, Menu, BrowserWindow, ipcMain, dialog } = require('electron');
const fs = require('fs');

// Local module
// const commoner = require('./renderer-process/common');

// Keep a global reference of the window object, if you don't, the window will
// be closed automatically when the JavaScript object is garbage collected.
let mainWindow;

// Variables with the processes IDs
let all_pids = { 'pids':[], 'c_pids':[] };

// Menu
let template = [
  { label: "Menu", submenu: [    
    { label: 'Main Page', click() { mainWindow.loadFile('index.html') } },
    // { label: "Open Model Project", submenu: [
    //   { label: 'Integration WT/KO - iTRAQ Reagent 8 plex kit', click() { mainWindow.loadURL(`file://${__dirname}/wf.html?ptype=samples&pdir=${process.env.ISANXOT_LIB_HOME}/samples/basic.wt_ko`) } },
    //   { label: 'Label-Free - MaxQuant', click() { mainWindow.loadURL(`file://${__dirname}/wf.html?ptype=samples&pdir=${process.env.ISANXOT_LIB_HOME}/samples/basic.lblfree`) } },
    //   { label: 'New Project', accelerator: 'Ctrl+N', click() { mainWindow.loadURL(`file://${__dirname}/wf.html?ptype=load&pdir=${__dirname}/wfs/basic`) } },
    // ]},  
    { id: 'new-project', label: 'New Project...', accelerator: 'Ctrl+N', click() { mainWindow.webContents.send('newProject') } },
    { id: 'open-project', label: 'Open Project...', accelerator: 'Ctrl+O', click() { mainWindow.webContents.send('openProject') } },
    { id: 'save-project', label: 'Save Project', accelerator: 'Ctrl+S', enabled: false, click() { mainWindow.webContents.send('saveProject') } },
    { type: 'separator' },
    { id: 'import-workflow', label: 'Import Workflow...', enabled: false, click() { mainWindow.webContents.send('importWorkflow') } },
    { id: 'export-workflow', label: 'Export Workflow As...', enabled: false, click() { mainWindow.webContents.send('exportWorkflow') } },
    { type: 'separator' },
    { id: 'exit', label: 'Exit', accelerator: 'Shift+Ctrl+Q', click() { mainWindow.close() } }
  ]},
  { id: "adaptors", label: "Adaptors", enabled: false, submenu: []},
  { id: "processes", label: "Processes", enabled: false, submenu: [
    { id: "processes-main", label: 'Main page', enabled: false, click() { mainWindow.loadFile('processes.html') } }
  ]},
  { label: "Help", submenu: [
    { label: 'General', click() { mainWindow.loadURL(`file://${__dirname}/help.html`) } },    
    { label: 'Workflows', submenu: [
      { label: 'Basic', click() { mainWindow.loadURL(`file://${__dirname}/help.html#help_basic`) } },
    ]},
    { label: 'Commands', click() { mainWindow.loadURL(`file://${__dirname}/commands.html`) } },
  ]},
]

// Add Adaptor menus
// This function handles arrays and objects recursively
function addClickFuncRecursively(obj) {
  for (var k in obj) {
    if ( obj[k] !== null && typeof obj[k] == "object" && !('clicked' in obj[k]) ) {
      addClickFuncRecursively(obj[k]);
    }
    else if ( obj[k] !== null && typeof obj[k] == "object" && 'clicked' in obj[k] ) {
      // add the function for click event
      obj[k].click = function(menu) {
        mainWindow.webContents.send('importAdaptor', menu.clicked) };
    }
  }
}
let adaptor_menu = JSON.parse(fs.readFileSync(`${__dirname}/adaptors/menu.json`));
addClickFuncRecursively(adaptor_menu);
template[1]['submenu'] = adaptor_menu;
// console.log(JSON.stringify(adaptor_menu, null, 4));



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
function createWindow () {
  // Create the browser window.
  mainWindow = new BrowserWindow({
    minWidth: 1074,
    minHeight: 850,
    width: 1250,
    height: 850,
    webPreferences: {
      nodeIntegration: true,
      contextIsolation: false,
      enableRemoteModule: true
    },
    // resizable: false,
    'icon': __dirname + '/assets/icons/molecule.png',
  })

  // and load the index.html of the app.
  mainWindow.loadFile('index.html')

  // Debug mode
  if (process.env.ISANXOT_MODE == "debug") {
    mainWindow.webContents.openDevTools();
  }
  else { // Remove console log in production mode
    console.log = function() {};
  }

  mainWindow.focus()

  // Emitted when the window is starting to be close.
  mainWindow.on('close', function(event) {
    console.log("** close windows");
    let choice = reallyWantToClose();
    console.log("   event prevent");
    if (choice === 1) event.preventDefault();  
  })

  // // Emitted when the window is closed.
  // mainWindow.on('closed', function(e) {
  //   console.log("** closed windows");
  //   // Dereference the window object, usually you would store windows
  //   // in an array if your app supports multi windows, this is the time
  //   // when you should delete the corresponding element.
  //   mainWindow = null;
  //   app.quit();  
  // })
  
  // Set application menu
  Menu.setApplicationMenu(menu)

}; // end createWindow

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


/*
App functions
*/

// This method will be called when Electron has finished initialization 
// and is ready to create browser windows.
// Some APIs can only be used after this event occurs.
// app.on('ready', createWindow);
app.on('ready', function (event) {
  console.log("** ready");
  createWindow();
  // app on top
  mainWindow.setAlwaysOnTop(true);
  // once a time, we get off the top
  setTimeout(function() {
    mainWindow.setAlwaysOnTop(false);
  },1000);
});

app.on('activate', function () {
  console.log("** activate");
  // On OS X it's common to re-create a window in the app when the
  // dock icon is clicked and there are no other windows open.
  if (mainWindow === null) {
    createWindow();
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
  app.quit();
});


// ---------------

// In this file you can include the rest of your app's specific main process
// code. You can also put them in separate files and require them here.

// Load the new URL
ipcMain.on('load-page', function(event, arg) {
  mainWindow.loadURL(arg);
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
