/*
 * Import libraries
 */
let fs = require('fs');
const { BrowserWindow, dialog } = require('electron').remote;
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
            title: 'iSanXoT! Help',
            width: 600,
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
        // helpWindow.webContents.openDevTools();
        // helpWindow.once('ready-to-show', () => {
        //     helpWindow.show();
        // });
        helpWindow.show();
    }
    helpWindow.loadURL(`${__dirname}/../help.html#${type}`).catch( (error) => {
        // console.log(error);
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

