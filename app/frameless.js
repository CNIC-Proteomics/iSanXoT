const { app, BrowserWindow } = require("electron");
const path = require("path");

// Menu
let template = [
    { label: "Menu", submenu: [    
        { id: 'main-page',    label: 'Main Page', click() { mainWindow.loadFile('index.html') } },
        { id: 'new-project',  label: 'New Project...', accelerator: 'Ctrl+N', click() { mainWindow.webContents.send('newProject') } },
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
        { id: 'help-intro', label: 'Introduction', click() { mainWindow.webContents.send('openHelper', 'help_intro') } },
        { id: 'help-cmds', label: 'Commands', click() { mainWindow.webContents.send('openHelper', 'help_cmds') } },
        { label: 'Workflows', submenu: [
        { id: 'help-wf_basic', label: 'Basic', click() { mainWindow.webContents.send('openHelper', 'help_wf-basic') } },
        { id: 'help-wf_ptm', label: 'PTM', click() { mainWindow.webContents.send('openHelper', 'help_wf-ptm') } }
        ]}
    ]},
];

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
        'icon': `${__dirname}/assets/icons/molecule.png`,
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

    // Set application menu
    Menu.setApplicationMenu(menu)

}; // end createWindow
  
const loadMainWindow = () => {
    const mainWindow = new BrowserWindow({
        width: 800,
        height: 600,
        frame: false,
        webPreferences: {
            nodeIntegration: true,
            contextIsolation: false,
            enableRemoteModule: true
        }
    });

    mainWindow.loadFile(path.join(__dirname, "frameless.html"));

    mainWindow.webContents.openDevTools();

    // Emitted when the window is starting to be close.
    mainWindow.on('close', function(event) {
        console.log("** close frameless");
        createWindow();
        // let choice = reallyWantToClose();
        // console.log("   event prevent");
        // if (choice === 1) event.preventDefault();
    });
    
    // // Emitted when the window is closed.
    // mainWindow.on('closed', function(e) {
    //   console.log("** closed windows");
    //   // Dereference the window object, usually you would store windows
    //   // in an array if your app supports multi windows, this is the time
    //   // when you should delete the corresponding element.
    //   mainWindow = null;
    // //   app.quit();
    // })
    
};


app.on("ready", () => {
console.log("** ready");
    loadMainWindow();
});

app.on("window-all-closed", () => {
console.log("** window-all-closed");
    if (process.platform !== "darwin") {
        app.quit();
    }
});

app.on("activate", () => {
console.log("** activate");
    if (BrowserWindow.getAllWindows().length === 0) {
        loadMainWindow();
    }
});
