/*
 * Import libraries
 */
let path = require('path');
let url = require('url');
const { BrowserWindow } = require('electron').remote;
const mainWindow = BrowserWindow.getFocusedWindow();

/*
 * Variables
 */
var helpWindow = undefined;


/*
 * Local functions
 */

// New project folder: open new window that saves the project name in a folder
function openHelper(type) {
    if ( helpWindow === undefined || helpWindow.isDestroyed() ) {
        helpWindow = new BrowserWindow({
            title: 'iSanXoT Help',
            width: 900,
            height: 800,
            webPreferences: {
                nodeIntegration: true,
                contextIsolation: false,
                enableRemoteModule: true
            },
            minimizable: true,
            resizable: true,
            'icon': process.env.ISANXOT_ICON,
            parent: mainWindow,
            show: false
        });
        helpWindow.setMenu(null);
        helpWindow.show();
    }
    // debug mode
    if (process.env.ISANXOT_MODE == "debug") {
        helpWindow.webContents.openDevTools();
    }
    helpWindow.loadURL(
        url.format({
            protocol: 'file',
            slashes: true,
            pathname: path.join(__dirname, `../help.html`),
            hash: type
        })
    ).catch( (error) => {
        console.log(error);
    });
}

/*
 * Export functions
 */

module.exports = {
    openHelper: openHelper
};

/*
 * Renderer functions
 */

const { ipcMain } = require('electron').remote;

// Renderer functions from the window "create New Project"
ipcMain.on('newprojectsubmit', (event, data) => {
    // get given data
    projectname = data.name;
    projectfolder = data.folder;
});

/*
 * Import libraries
 */

