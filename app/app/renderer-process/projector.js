/*
 * Import libraries
 */
let fs = require('fs');
let path = require('path');
const { BrowserWindow } = require('electron').remote;
const mainWindow = BrowserWindow.getFocusedWindow();

/*
 * Variables
 */

// get given data
let projectname = undefined;
let projectfolder = undefined;


/*
 * Local functions
 */

// Get the workflow name
function getProjectCfg(dir) {
    let prj_cfg =  undefined;
    // get most recent dir
    dir = `${dir}/.isanxot`;
    if (!fs.existsSync(dir) ) return undefined;
    let id = commoner.getMostRecentDir(dir);
    if ( id !== undefined ) {
        dir = `${dir}/${id}`;
        // get the workflow config if exits.
        let prj_cfgfile = `${dir}/config.yaml`;
        prj_cfg =  ( fs.existsSync(prj_cfgfile) ) ? jsyaml.safeLoad( fs.readFileSync(`${prj_cfgfile}`, 'utf-8')) : undefined;
    }
    return prj_cfg;
}

// Get a string with the local date
function getWFDate() {
    let d = new Date();
    d.setDate(d.getDate());
    Y = d.getFullYear();
    M = ('0' + (d.getMonth()+1)).slice(-2)
    D = ('0' + d.getDate()).slice(-2)
    h = ('0' + d.getHours()).slice(-2)
    m = ('0' + d.getMinutes()).slice(-2);
    s = ('0' + d.getSeconds()).slice(-2);
    return Y+M+D+h+m+s;
}

// Prepare the root folder of project
function preparePrjDir(name, basefolder) {
    // create the project folder
    let prj_rootdir = `${basefolder}/${name}`;
    try {
        if ( !fs.existsSync(`${prj_rootdir}`) ) {
            fs.mkdirSync(`${prj_rootdir}`, {recursive: true} );
        }
    } catch (err) {    
        exceptor.showMessageBox('error',`${prj_rootdir}: ${err}`, title='Creating directory', end=true);
    }
    return prj_rootdir;
}

// Prepare the project workspace
function preparePrjWorkspace(prj_id, prj_rootdir) {
    // extract the project attributes
    let wfs = JSON.parse(fs.readFileSync( path.join(process.env.ISANXOT_WFS_HOME, 'commands.json') ));
    let prj_dirs = wfs['prj_workspace'];

    // create the directories for the project
    for ( let k in prj_dirs ) {
        let ws = prj_dirs[k];
        let prj_dir = `${prj_rootdir}/${ws}`;
        try {
            if ( !fs.existsSync(`${prj_dir}`) ) {
                fs.mkdirSync(`${prj_dir}`, {recursive: true} );
            }
        } catch (err) {    
            exceptor.showMessageBox('error',`${prj_dir}: ${err}`, title='Creating directory', end=true);
        }
    }
    // create log directory for the current execution
    let log_dir = `${prj_rootdir}/${prj_dirs['logdir']}/${prj_id}`;
    try {
        if ( !fs.existsSync(`${log_dir}`) ) {
            fs.mkdirSync(`${log_dir}`, {recursive: true} );
        }
    } catch (err) {    
        console.log(log_dir);
        exceptor.showMessageBox('error',`${log_dir}: ${err}`, title='Creating logging directory', end=true);
    }
    return log_dir;
}

// Export prject dfg file
function exportProjectCfg(prj_id, prj_dir, cfg_dir, wf) {
    // Create config file with basic parameters of workflow
    let cfg = {
        'name': wf['id'],                
        'version': require('electron').remote.app.getVersion(),
        'date': prj_id,
        'ncpu': document.querySelector('#nthreads').value,
        'verbose': '-vv'
    };
    // Add the directories for the project
    cfg['prj_workspace'] = {};
    let wfs = JSON.parse(fs.readFileSync( path.join(process.env.ISANXOT_WFS_HOME, 'commands.json') ));
    for (let ws in wfs['prj_workspace']) {
        cfg['prj_workspace'][ws] = `${prj_dir}/${wfs['prj_workspace'][ws]}`;
    }
    // Check if commands are available correctly
    for (var h = 0; h < wf['tabs'].length; h++) { // go through tabs
        let tab = wf['tabs'][h];
        for (var i = 0; i < tab['works'].length; i++) { // go through works
            let wk = tab['works'][i];    
            for (var j = 0; j < wk['cmds'].length; j++) { // go through cmds
                let cmd = wk['cmds'][j];
                let cmd_id = cmd['id'];
                let incmds = {};
                if ( !('inpcmds' in cfg) ) { cfg['inpcmds'] = []; }
                // create params (mostly for adaptor)
                if ( 'params' in cmd ) {
                    let cmd_params = [];
                    for (let k=0; k < cmd['params'].length; k++) {
                        let param = cmd['params'][k];
                        if ( $(`#${param}`).length > 0 && $(`#${param}`).val() != '' ) {
                            cmd_params.push({
                                'key': param,
                                'val': $(`#${param}`).val()
                            });    
                        }
                    }
                    if ( cmd_params.length > 0 ) incmds['params'] = cmd_params;
                }
                // create the tasktables
                if ( 'tasktable' in cmd ) {
                    let cmd_ttables = [];
                    for (let k=0; k < cmd['tasktable'].length; k++) {
                        let ttable = cmd['tasktable'][k];
                        let cmd_ttable_id = ('id' in ttable) ? ttable['id'] : cmd_id.toLowerCase();
                        if ( 'file' in ttable ) {
                            let f = `${cfg_dir}/${ttable['file']}`;
                            if ( fs.existsSync(f) ) {
                                cmd_ttables.push({
                                    'id': cmd_ttable_id,
                                    'file': f
                                });
                            }
                        }
                    }
                    if ( cmd_ttables.length > 0 ) incmds['ttables'] = cmd_ttables;
                }
                // add to cfg
                if ( Object.keys(incmds).length > 0 ) {                    
                    cfg['inpcmds'].push(Object.assign({'name': cmd_id}, incmds));
                }
            }
        }
    }

    // Sort the input commands from the list of commands (json)
    // get the list of commands
    let [rst,cnt] = commoner.getIndexParamsWithKey(wfs['commands'], 'id');
    // sort the input commands based the list of commands
    cfg['inpcmds'] = commoner.sortListObjFromListVals(cfg['inpcmds'], 'name', cnt);


    // Write cfg file sync
    let cfgfile = `${cfg_dir}/.cfg.yaml`;
    let cfgcont = jsyaml.safeDump(cfg);
    try {
        fs.writeFileSync(cfgfile, cfgcont, 'utf-8');
    } catch (err) {    
        exceptor.showErrorMessageBox('Error Message', `Writing the config file ${cfgfile}: ${err}`, end=true);
    }
    return cfgfile;
}
      
// New project folder: open new window that saves the project name in a folder
function newProject() {
    let win = new BrowserWindow({
        title: 'Create new project',
        width: 700,
        height: 250,
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
    win.loadFile(`${__dirname}/../new-project.html`);
    // win.webContents.openDevTools();
    win.on('close', function () {
        win = null;
        if ( projectname !== undefined && projectfolder !== undefined ) {
            // create the root folder of project
            projectfolder = preparePrjDir(projectname, projectfolder);
            // create new project id
            let projectid = getWFDate();
            // load the initial workflow (empty task-tables)
            workflower.loadWorkflow(projectid, projectfolder);
        // } else {
        //     exceptor.showMessageBox('warning',`The project has not been created`, title='Create new project', end=true);
        }
    });
    win.show();    
}

// Open project folder (sync). Assign the folder with the project samples by default.
function openProject(prj_dir) {
    // assgin the first value
    if ( prj_dir.length > 0 ) prj_dir = prj_dir[0];
    // create new project id
    let prj_id = getWFDate();
    // get the workflow directory (the most recent).
    let wkf_dir = workflower.getWorkflowDir(prj_dir);
    if ( wkf_dir === undefined ) {
        exceptor.showMessageBox('error',`The workflow directory is not defined`, title='Opening project', end=false);
    }
    else {
        // // get the adaptor directory
        let adp_dir = process.env.ISANXOT_ADAPTOR_HOME;
        // check if the workflow folder is 'date_id'. This means, the given directory comes from workflow folder.
        // assign project_dir to undefined to force an exception.
        let wf_id = wkf_dir.match(/([^\/]*)\/*$/)[1];
        if ( wf_id == 'date_id' ) prj_dir = undefined;
        // load the project with the last workflow
        workflower.loadWorkflow(prj_id, prj_dir, wkf_dir, adp_dir);
    }
}

function saveProject() {
    // check adaptor inputs
    // return project folder
    let [prj_dir, adp_cmds, ] = checkAdaptorInputs(exceptor);
    if (adp_cmds && prj_dir) {
        // get input parameters (from URL)
        let url_params = new URLSearchParams(window.location.search);
        let prj_id = url_params.get('pid');
        if (prj_id === undefined) prj_id = 'date_id';
        let adp_dir = url_params.get('adir');
        // prepare the workspace of project
        let cfg_dir = workflower.prepareWfWorkspace(prj_id, prj_dir);
        // get the workflow structure
        let wkf = workflower.extractWorkflowStr();
        // get the adaptor structure
        let adp = workflower.extractAdaptorStr(adp_dir, adp_cmds);
        // join the adaptor strcuture and workflow structure
        let wf = workflower.joinWorkflowAdaptorStr(adp, wkf);
        // export workflow Commands
        workflower.exportWorkflowCmds(cfg_dir, wf);
        // export project cfg file
        let wf_cfgfile = exportProjectCfg(prj_id, prj_dir, cfg_dir, wf);
        // create the root folder of project. Here, the variable contains completed path.
        projectfolder = preparePrjDir('', prj_dir);
        // Exec: create config file for the execution of workflow
        executor.execTable2Cfg({
            'indir': cfg_dir,
            'attfile': wf_cfgfile,
            'outfile': `${cfg_dir}/config.yaml`,
            'logdir': cfg_dir
        });
        return [prj_id, prj_dir, cfg_dir];
    }
    else return [undefined,undefined,undefined];
}

/*
 * Export functions
 */

module.exports = {
    getProjectCfg: getProjectCfg,
    preparePrjWorkspace: preparePrjWorkspace,
    newProject: newProject,
    openProject: openProject,
    saveProject: saveProject
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

let exceptor = require('./exceptor');
let commoner = require('./common');
let workflower = require('./workflower');
let executor = require('./executor');
