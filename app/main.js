// Modules to control application life and create native browser window
const { app, Menu, BrowserWindow, ipcMain, dialog } = require('electron');

// Keep a global reference of the window object, if you don't, the window will
// be closed automatically when the JavaScript object is garbage collected.
let mainWindow;

// Variables with the processes IDs
let all_pids = { 'pids':[], 'c_pids':[] };

// Menu
let template = [
  { label: "Menu", submenu: [    
    { label: 'Main Page', click() { mainWindow.loadFile('index.html') } },
    { label: 'Open Project...', accelerator: 'Ctrl+O', click() { mainWindow.webContents.send('openProject') } },
    { label: 'Save Project', accelerator: 'Ctrl+S', click() { mainWindow.webContents.send('saveProject') } },
    { label: 'Validate Project', accelerator: 'Ctrl+Shift+V', click() { mainWindow.webContents.send('validateProject') } },
    { type: 'separator' },
    { label: 'Exit', accelerator: 'Shift+Ctrl+Q', click() { mainWindow.close() } }
  ]},
  { label: "Workflows", submenu: [
    { label: 'Basic', submenu: [
      // { label: 'Basic - Init', click() { mainWindow.loadURL(`file://${__dirname}/wf.html?wfid=basic`) } },
      { label: 'from scratch', click() { mainWindow.loadURL(`file://${__dirname}/wf.html?wfid=load&pdir=${__dirname}/wfs/basic/init`) } },
      { label: 'with a sample', click() { mainWindow.loadURL(`file://${__dirname}/wf.html?wfid=load&pdir=${__dirname}/wfs/basic/sample`) } },
    ]},
    { label: 'PTM', submenu: [
      // { label: 'PTM Mode', click() { mainWindow.loadURL(`file://${__dirname}/wf.html?wfid=ptm`) } },
      { label: 'from scratch', click() { mainWindow.loadURL(`file://${__dirname}/wf.html?wfid=load&pdir=${__dirname}/wfs/ptm/init`) } },
      { label: 'with a sample', click() { mainWindow.loadURL(`file://${__dirname}/wf.html?wfid=load&pdir=${__dirname}/wfs/ptm/sample`) } },
    ]},
    // { label: 'Label-Free Mode', click() { mainWindow.loadURL(`file://${__dirname}/wf.html?wfid=lblfree`) } },
  ]},
  { label: "Processes", submenu: [
    { label: 'Main page', click() { mainWindow.loadFile('processes.html') } }
  ]},
  // { label: "Preferences", submenu: [
  //   { label: 'Download Databases', click() { mainWindow.loadFile('downdb.html') } },
  //   { label: 'Check for Updates', click() { mainWindow.loadFile('checkupdates.html') } },
  // ]},  
  { label: "Help", submenu: [
    { label: 'General', click() { mainWindow.loadFile('help.html') } },
    { label: 'Basic workflow', click() { mainWindow.loadURL(`file://${__dirname}/help.html#help_basic`) } },
    { label: 'PTM workflow', click() { mainWindow.loadURL(`file://${__dirname}/help.html#help_ptm`) } },
    // { label: 'Label-Free workflow', click() { mainWindow.loadURL(`file://${__dirname}/help.html#help_lblfree`) } }
  ]},  
]
// Add 'debugging' menu
if (process.env.ISANXOT_MODE != "production") {
  template.push({ label: "Debug", submenu: [
    { label: 'Reload', accelerator: 'Ctrl+R', click() { mainWindow.reload() } },
    { label: 'Toggle Developer Tools', accelerator: 'Ctrl+D', click() { mainWindow.webContents.openDevTools() } }
  ]});
}
// create menu
const menu = Menu.buildFromTemplate(template)

/*
Local functions
*/

// Create the main Window
function createWindow () {
  // Create the browser window.
  mainWindow = new BrowserWindow({
    'minWidth': 1074,
    'minHeight': 850,
    'width': 1250,
    'height': 850,
    'webPreferences': {
      'nodeIntegration': true
    },
    // resizable: false,
    'icon': __dirname + '/assets/icons/molecule.png',
  })

  // and load the index.html of the app.
  mainWindow.loadFile('index.html')

  // Remove console log in production mode
  if (process.env.ISANXOT_MODE == "production") {
    console.log = function() {};
  }
  else { // Debug mode    
    mainWindow.webContents.openDevTools()
  }

  mainWindow.focus()

  // Emitted when the window is starting to be close.
  mainWindow.on('close', function(event) {
    console.log("** close1 windows");
    let choice = reallyWantToClose();
    if (choice === 1) event.preventDefault();  
  })

  // Emitted when the window is closed.
  mainWindow.on('closed', function(e) {
    // Dereference the window object, usually you would store windows
    // in an array if your app supports multi windows, this is the time
    // when you should delete the corresponding element.
    console.log("** close2 windows");
    mainWindow = null
    app.quit();  
  })
  
  // Set application menu
  Menu.setApplicationMenu(menu)

}; // end createWindow

// // local function: add the project folder
// function addInputsFileDirectoy(inputs, errsms) {
//   if(inputs === undefined) {
//     console.log(`${errsms}: input is undefined`);
//     exceptor.showErrorMessageBox('Error Message', `${errsms}`);
//   }
//   else if (inputs.canceled) {
//     console.log(`${errsms}: canceled operation`);
//   }
//   else if (!('filePaths' in inputs )) {
//     console.log(`${errsms}: filePaths does not defined`);
//     exceptor.showErrorMessageBox('Error Message', `${errsms}`);
//   }
//   else {
//     if ( inputs['filePaths'].length == 0 ) {
//       console.log(`${errsms}: filePaths is empty`);
//       exceptor.showErrorMessageBox('Error Message', `${errsms}`);
//     }
//     else {
//       let file = inputs['filePaths'][0];
//       mainWindow.loadURL(`file://${__dirname}/wf.html?wfid=load&pdir=${file}`);
//     }
//   }
// };

// // Load project folder
// function openProject() {
//   // Select a folder: Asynchronous - using callback
//   // Use the main window to be modal
//   let opts = { properties: ["openDirectory"] };
//   dialog.showOpenDialog(mainWindow, opts).then((dirs) => {
//     isOpenLoadProjectDialog = false;
//     addInputsFileDirectoy(dirs, `No project folder selected`);
//   });
// };

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
  console.log(`kill child processes: ${all_pids['c_pids']}`);
  all_pids['c_pids'].reverse().forEach(function(pid) {
    try {
      console.log(`${pid} has been killed!`);
      process.kill(pid);
    }
    catch (e) {
      console.log(`error killing ${pid}: ${e}`);
    }
  });
  console.log(`kill processes: ${all_pids['pids']}`);
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
  console.log("ready");
  createWindow();
  // app on top
  mainWindow.setAlwaysOnTop(true);
  // once a time, we get off the top
  setTimeout(function() {
    mainWindow.setAlwaysOnTop(false);
  },1000);

  // console.log("ready 2");

});



// before quit: App close handler
app.on('before-quit', function (event) {
  console.log("** before-quit");
  mainWindow.removeAllListeners('close');
  mainWindow.close();  
});

// When all windows are closed...
app.on('window-all-closed', function () {
  // kill all processes
  console.log("** kill all processes");
  KillProcceses(all_pids);
});

app.on('activate', function () {
  // On OS X it's common to re-create a window in the app when the
  // dock icon is clicked and there are no other windows open.
  if (mainWindow === null) {
    createWindow()
  }
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
