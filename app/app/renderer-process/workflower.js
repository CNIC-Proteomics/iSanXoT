/*
 * Import libraries
 */

let fs = require('fs');
let path = require('path');
let url = require('url');
const { BrowserWindow } = require('electron').remote;
var mainWindow = BrowserWindow.getFocusedWindow();

/*
 * Local functions
 */

// Get the Cfg file of workflow
function getWorkflowCfg(wkf_dir) {
  // get the workflow config if exits.
  let wf_cfgfile = `${wkf_dir}/.cfg.yaml`;
  let wf_cfg = ( fs.existsSync(wf_cfgfile) ) ? jsyaml.safeLoad( fs.readFileSync(`${wf_cfgfile}`, 'utf-8')) : undefined;
  return wf_cfg;
}

// Get the workflow directory (the most recent).
function getWorkflowDir(dir) {
  let wkf_dir = undefined;
  dir = `${dir}/.isanxot`;
  if (!fs.existsSync(dir) ) return wkf_dir;
  // get most recent dir
  let id = commoner.getMostRecentDir(dir);
  if (id) wkf_dir = `${dir}/${id}`;
  return wkf_dir;
}

// Extract the information of workflow
// Go through the works of the workflow and fill the information of work and commands
function extractWorkflowStr() {
  // extract the project attributes
  let wkf = JSON.parse(fs.readFileSync( path.join(process.env.ISANXOT_WFS_HOME, 'commands.json') ));
  // create the information of tabs/works/cmds for the workflow
  for (var i = 0; i < wkf['tabs'].length; i++) {
    for (var j = 0; j < wkf['tabs'][i]['works'].length; j++) {
      for (var k = 0; k < wkf['tabs'][i]['works'][j]['cmds'].length; k++) {
          let cmd_id = wkf['tabs'][i]['works'][j]['cmds'][k];
          // extract the info of cmd
          let cmd = commoner.getObjectFromID(wkf['commands'], cmd_id);
          // replace the info cmd
          wkf['tabs'][i]['works'][j]['cmds'][k] = cmd;
      }
    }
  }
  return wkf;
}

// Extract the structure of adaptor
// Go through the works of the adaptor and fill the information of work and commands
function extractAdaptorStr(adp_dir, adp_cmds) {
  // extract the project attributes
  let wkf = JSON.parse(fs.readFileSync(path.join(adp_dir, process.env.ISANXOT_ADAPTOR_TYPE)));
  // create the information of tabs/works/cmds for the workflow
  for (var i = 0; i < wkf['tabs'].length; i++) {
    for (var j = 0; j < wkf['tabs'][i]['works'].length; j++) {
      // redifine the list of cmds for the adaptor
      let new_cmds = [];
      for (var k = 0; k < wkf['tabs'][i]['works'][j]['cmds'].length; k++) {
          let cmd_id = wkf['tabs'][i]['works'][j]['cmds'][k];
          // if adp_cmds is defined  => get only the cmds in the list
          if ( adp_cmds ) {
            if ( adp_cmds.length > 0 && adp_cmds.includes(cmd_id) ) {
              let cmd = commoner.getObjectFromID(wkf['commands'], cmd_id);
              new_cmds.push(cmd);
            }            
          }
          // if adp_cmds is not defined => extract all cmds
          else {
            let cmd = commoner.getObjectFromID(wkf['commands'], cmd_id);
            new_cmds.push(cmd);
          }          
      }
      if ( new_cmds && new_cmds.length > 0 ) wkf['tabs'][i]['works'][j]['cmds'] = new_cmds;
    }
  }
  return wkf;
}

// Join the adaptor structure and workflow structure
function joinWorkflowAdaptorStr(adp, wkf) {
  let wf = wkf;
  for (let i = adp['tabs'].length -1; i >= 0; i--) {
    wf['tabs'].unshift(adp['tabs'][i]);
  }
  for (let i = adp['commands'].length -1; i >= 0; i--) {
    wf['commands'].unshift(adp['commands'][i]);
  }
  return wf;
}

// Prepare the config folder for workflow-project
function prepareWfWorkspace(date_id, outdir) {
  // declare variables
  let cfg_dir = `${outdir}/.isanxot/${date_id}`;
  // check the output directory
  if ( outdir == "" ) {
      exceptor.showMessageBox('error',`The workflow directory is empty`, title='Preparing workflow workspace', end=true);
  }
  // create configuration directory (hidden) for the current execution    
  try {
      if ( !fs.existsSync(`${cfg_dir}`) ) {
          fs.mkdirSync(`${cfg_dir}`, {recursive: true} );
      }
  } catch (err) {    
      console.log(cfg_dir);
      exceptor.showMessageBox('error',`${cfg_dir}: ${err}`, title='Preparing workflow workspace', end=true);
  }
  return cfg_dir;
}

// Export tasktable to TSV
function exportTasktable(tsk_id, header_ids, header_names) {
  // init output
  let cont = '';
  // check if table is empty
  let numEmptyRows = $(`${tsk_id}`).handsontable('countEmptyRows');
  let numRows = $(`${tsk_id}`).handsontable('countRows');
  if ( numRows > numEmptyRows ) {
      // rename header with the header_ids
      $(`${tsk_id}`).handsontable('updateSettings', {'colHeaders': header_ids });
      let exportPlugin = $(`${tsk_id}`).handsontable('getPlugin', 'exportFile');
      cont = exportPlugin.exportAsString('csv', {
          mimeType: 'text/csv',
          columnDelimiter: '\t',
          columnHeaders: true,
          exportHiddenColumns: true,
          bom: false
      });
      // rename column with header names
      $(`${tsk_id}`).handsontable('updateSettings',{'colHeaders': header_names });
  }
  return cont;
}

// Export the workflow commnands
function exportWorkflowCmds(cfg_dir, wf) {

  for (var h = 0; h < wf['tabs'].length; h++) { // go through tabs
    let tab = wf['tabs'][h];
    for (var i = 0; i < tab['works'].length; i++) { // go through works
      let wk = tab['works'][i];
      let wk_id = wk['id'];
      // concatenate the data table of all commands
      for (var j = 0; j < wk['cmds'].length; j++) { // go through cmds
        let cmd = wk['cmds'][j];
        let cmd_id = cmd['id'];
        // create tasktables
        if ( 'tasktable' in cmd ) {
          for (let k=0; k < cmd['tasktable'].length; k++) {
            let ttable = cmd['tasktable'][k];
            let ttable_id = ttable['id'];
            let ttable_file = `${cfg_dir}/${ttable['file']}`;
            if ( 'params' in ttable ) {
              // get the id header based on 'commands.json'
              let header_ids = [];
              let header_names = [];
              try {
                header_ids = ttable['params'].map(a => a.id);
                if (header_ids.includes(undefined)) {
                    throw "the list of id headers contains undefined value";
                }
              } catch (err) {
                exceptor.showErrorMessageBox('Error Message', `Extracting the id headers of ${cmd_id}: ${err}`, end=true);
              }
              // get the header names based on 'commands.json'
              try {
                header_names = ttable['params'].map(a => a.name);
                if (header_names.includes(undefined)) {
                    throw "the list of id headers contains undefined value";
                }
              } catch (err) {
                exceptor.showErrorMessageBox('Error Message', `Extracting the names headers of ${cmd_id}: ${err}`, end=true);
              }
              // export tasktable to CSV
              let cont = '';
              try {
                if ( $(`#page-cmd-${cmd_id} #page-ttable-${ttable_id} .tasktable`).length ) {
                    cont = exportTasktable(`#page-cmd-${cmd_id} #page-ttable-${ttable_id} .tasktable`, header_ids, header_names);
                }
              } catch (err) {
                  exceptor.showErrorMessageBox('Error Message', `Exporting the command table ${cmd_id}: ${err}`, end=true);    
              }
              // if not empty write tasktable file sync
              if ( cont != '' ) {
                  try {
                      fs.writeFileSync(ttable_file, cont, 'utf-8');
                  } catch (err) {    
                      exceptor.showErrorMessageBox('Error Message', `Writing the tasktable file: ${err}`, end=true);    
                  }
              }
              // if empty table, remove file sync if exists
              else {
                try {
                  if ( fs.existsSync(ttable_file) ) fs.unlinkSync(ttable_file, cont, 'utf-8');
                } catch (err) {    
                    exceptor.showErrorMessageBox('Error Message', `Updating the tasktable file: ${err}`, end=true);    
                }
              }
            }
          } // end for loop ttable
        } // end if ( 'tasktable' in cmd )
      } // end for loop cmds
    } // end for loop works
  } // // end for loop tabs
}

// Add workflow workspace
function loadWorkflow(prj_id, prj_dir, wkf_dir, adp_dir) {
  // project id is required
  if (prj_id === undefined || prj_id == '') exceptor.showErrorMessageBox('Error Message', `The project id is not defined`, end=true);
  // project folder is required
  if (prj_dir === undefined || prj_dir == '') exceptor.showErrorMessageBox('Error Message', `The project folder is not defined`, end=true);
  // adaptor folder. By default, the main_input adaptor
  adp_dir = (adp_dir !== undefined && adp_dir != '')? adp_dir : process.env.ISANXOT_ADAPTOR_HOME;
  // required to load the project when comers from processes frontpage
  if(!mainWindow) {
    var BrowserWindow = require('electron').remote;
    // mainWindow = BrowserWindow.getFocusedWindow();
    mainWindow = BrowserWindow.getCurrentWindow();
  }
  // load workflow
  console.log(`${__dirname}/../wf.html?pid=${prj_id}&pdir=${prj_dir}&wdir=${wkf_dir}&adir=${adp_dir}`);
  mainWindow.loadURL(
    url.format({
        protocol: 'file',
        slashes: true,
        pathname: path.join(__dirname, `../wf.html`),
        query: { "pid": prj_id, "pdir": prj_dir, "wdir": wkf_dir, "adir": adp_dir }
    })
  ).catch( (error) => {
        console.log(error);
  });
}

// Export only the task-tables of workflow
function exportWorkflow(wkf_dir) {
    // assgin the first value
    if ( wkf_dir.length > 0 ) wkf_dir = wkf_dir[0];
    // get the workflow structure
    let wf = extractWorkflowStr();
    // prepare the workspace of project
    let cfg_dir = prepareWfWorkspace('date_id', wkf_dir);
    // export workflow Commands
    exportWorkflowCmds(cfg_dir, wf);
}

// Import workflow from folder (sync). By default open the workflow samples folder.
function importWorkflow(wkf_dir) {
  // assgin the first value
  if ( wkf_dir.length > 0 ) wkf_dir = wkf_dir[0];
  // get the workflow directory (the most recent).
  wkf_dir = getWorkflowDir(wkf_dir);
  if ( wkf_dir === undefined ) {
    exceptor.showMessageBox('error',`The workflow directory is not defined`, title='Importing workflow', end=false);
  }
  else {
    // get input parameters (from URL)
    let url_params = new URLSearchParams(window.location.search);
    let prj_id = url_params.get('pid');
    let prj_dir = url_params.get('pdir');
    let adp_dir = url_params.get('adir');
    // add workflow workspace
    loadWorkflow(prj_id, prj_dir, wkf_dir, adp_dir);
  }
}

// Import adaptor from folder (sync). By default open the basic adaptor (main_input)
function importAdaptor(adp_dir) {
  // get input parameters (from URL)
  let url_params = new URLSearchParams(window.location.search);
  let prj_id = url_params.get('pid');
  let prj_dir = url_params.get('pdir');
  let wkf_dir = url_params.get('wdir');
  // add the absolute path to adaptor folder
  adp_dir = path.join(process.env.ISANXOT_ADAPTOR_HOME, adp_dir);
  // add workflow workspace
  loadWorkflow(prj_id, prj_dir, wkf_dir, adp_dir);
}


/*
 * Export functions
 */

module.exports = {
  getWorkflowCfg: getWorkflowCfg,
  getWorkflowDir: getWorkflowDir,
  extractWorkflowStr: extractWorkflowStr,
  extractAdaptorStr: extractAdaptorStr,
  joinWorkflowAdaptorStr: joinWorkflowAdaptorStr,
  prepareWfWorkspace: prepareWfWorkspace,
  exportWorkflowCmds: exportWorkflowCmds,
  loadWorkflow: loadWorkflow,
  exportWorkflow: exportWorkflow,
  importWorkflow: importWorkflow,
  importAdaptor: importAdaptor
};

/*
 * Import libraries
 */
let exceptor = require('./exceptor');
let commoner = require('./common');
