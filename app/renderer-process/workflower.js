/*
 * Import libraries
 */

let fs = require('fs');
const { BrowserWindow } = require('electron').remote;
var mainWindow = BrowserWindow.getFocusedWindow();

/*
 * Variables
 */

// Init workflow directory (with empty tables)
let initWkfDir = `${process.env.ISANXOT_SRC_HOME}/app/wfs/init`;

// Basic input adaptor (00_main_inputs)
let initAdpDir = `${process.env.ISANXOT_SRC_HOME}/app/adaptors/00_main_input`;

// Assign the folder with the project samples by default. Mandatory double slashes!!
let samplesWkfDir = `${process.env.ISANXOT_LIB_HOME}/samples`;
samplesWkfDir = samplesWkfDir.replace(/\//g, "\\");


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

// // Get the workflow name
// function getWorkflowName(wkf_dir) {
//   // get the workflow config if exits.
//   let wf_cfgfile = `${wkf_dir}/.cfg.yaml`;
//   let wf_cfg = ( fs.existsSync(wf_cfgfile) ) ? jsyaml.safeLoad( fs.readFileSync(`${wf_cfgfile}`, 'utf-8')) : undefined;
//   // get the workflow structure. By default we use basic workflow
//   let wf_name = (wf_cfg !== undefined && 'name' in wf_cfg) ? wf_cfg['name'] : 'basic';
//   return wf_name;
// }


// Get the workflow directory (the most recent). By default, init workflow
function getWorkflowDir(dir) {
  let wkf_dir = undefined;
  dir = `${dir}/.isanxot`;
  if (!fs.existsSync(dir) ) dir = `${initWkfDir}/.isanxot`;
  // get most recent dir
  let id = commoner.getMostRecentDir(dir);
  wkf_dir = (id) ? `${dir}/${id}` : getWorkflowDir(initWkfDir);
  return wkf_dir;
}

// Get the adaptor directory. By default, it is the basic adaptor (00_main_input)
function getAdaptorDir(wkf_dir) {
  // let adp_dir = undefined;
  // // if exists the adaptor config file,
  // // then get the adaptor id and report the adaptor folder
  // if ( fs.existsSync(`${wkf_dir}/adaptor.json`) ) {
    
  // }
  // // otherwise, reports the basic adaptor folder
  // else {
  //   adp_dir = initAdpDir;
  // }
  let adp_dir = (fs.existsSync(`${wkf_dir}/adaptor.json`)) ? wkf_dir : initAdpDir;
  return adp_dir;
}

// Extract the information of workflow
// Go through the works of the workflow and fill the information of work and commands
function extractWorkflowStr() {
  // extract the project attributes
  let wkf = JSON.parse(fs.readFileSync(`${__dirname}/../wfs/workflow.json`));
  // create the information of works for the workflow
  for (var i = 0; i < wkf['works'].length; i++) {
      // extract the information of commands for each work
      for (var j = 0; j < wkf['works'][i]['cmds'].length; j++) {
          let cmd_id = wkf['works'][i]['cmds'][j];
          // extract the info of cmd
          let cmd = commoner.getObjectFromID(wkf['commands'], cmd_id);
          // replace the info cmd
          wkf['works'][i]['cmds'][j] = cmd;
      }
  }
  return wkf;
}

// Extract the structure of adaptor
// Go through the works of the adaptor and fill the information of work and commands
function extractAdaptorStr(adp_dir) {
  // extract the project attributes
  let adp = JSON.parse(fs.readFileSync(`${adp_dir}/adaptor.json`));
  // create the information of works for the workflow
  for (var i = 0; i < adp['works'].length; i++) {
      // extract the information of commands for each work
      for (var j = 0; j < adp['works'][i]['cmds'].length; j++) {
          let cmd_id = adp['works'][i]['cmds'][j];
          // extract the info of cmd
          let cmd = commoner.getObjectFromID(adp['commands'], cmd_id);
          // replace the info cmd
          adp['works'][i]['cmds'][j] = cmd;
      }
  }  
  return adp;
}

// Join the adaptor strcuture and workflow structure
function joinWorkflowAdaptorStr(adp, wkf) {
  let wf = wkf;
  for (let i = adp['works'].length -1; i >= 0; i--) {
    wf['works'].unshift(adp['works'][i]);
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

  // Determines which adaptor is executed without tasktable ---
  // Create a tasktable for every command ---
  // Iterate over all the works of the workflow
  for (var i = 0; i < wf['works'].length; i++) {
      let wk = wf['works'][i];
      let wk_id = wk['id'];

      // concatenate the data table of all commands
      // iterate over all commands
      for (var j = 0; j < wk['cmds'].length; j++) {
          let cmd = wk['cmds'][j];
          let cmd_id = cmd['id'];
          // create a tasktable for every command
          if ( 'tasktable' in cmd && 'params' in cmd['tasktable'] ) {
              // get the id header based on 'workflow.json'
              let header_ids = [];
              let header_names = [];
              try {
                header_ids = cmd['tasktable']['params'].map(a => a.id);
                if (header_ids.includes(undefined)) {
                    throw "the list of id headers contains undefined value";
                }
              } catch (err) {
                exceptor.showErrorMessageBox('Error Message', `Extracting the id headers of ${cmd_id}: ${err}`, end=true);
              }
              // get the header names based on 'workflow.json'
              try {
                header_names = cmd['tasktable']['params'].map(a => a.name);
                if (header_names.includes(undefined)) {
                    throw "the list of id headers contains undefined value";
                }
              } catch (err) {
                exceptor.showErrorMessageBox('Error Message', `Extracting the names headers of ${cmd_id}: ${err}`, end=true);
              }
              // export tasktable to CSV
              let cont = '';
              try {
                if ( $(`#${wk_id} #page-tasktable-${cmd_id} .tasktable`).length ) {
                    let c = exportTasktable(`#${wk_id} #page-tasktable-${cmd_id} .tasktable`, header_ids, header_names);
                    if ( c != '' ) { cont += `\n#${cmd_id}\n${c}`; }
                }
              } catch (err) {
                  exceptor.showErrorMessageBox('Error Message', `Exporting the command table ${cmd_id}: ${err}`, end=true);    
              }
              // if not empty write tasktable file sync
              if ( cont != '' ) {
                  try {
                      let ttable_file = `${cfg_dir}/${cmd['tasktable']['file']}`;
                      fs.writeFileSync(ttable_file, cont, 'utf-8');
                  } catch (err) {    
                      exceptor.showErrorMessageBox('Error Message', `Writing the tasktable file ${ttable_file}: ${err}`, end=true);    
                  }    
              }
          }
      }
  }
}

// Add workflow workspace
function loadWorkflow(prj_id, prj_dir, wkf_dir, adp_dir) {
  // project id is required
  if (prj_id === undefined || prj_id == '') exceptor.showErrorMessageBox('Error Message', `The project id is not defined`, end=true);
  // project folder is required
  if (prj_dir === undefined || prj_dir == '') exceptor.showErrorMessageBox('Error Message', `The project folder is not defined`, end=true);
  // workflow folder. By default, a folder with empty tables
  wkf_dir = (wkf_dir !== undefined && wkf_dir != '')? wkf_dir : initWkfDir;
  // adaptor folder. By default, the main_input adaptor
  adp_dir = (adp_dir !== undefined && adp_dir != '')? adp_dir : initAdpDir;
  // required to load the project when comers from processes frontpage
  if(!mainWindow) {
    var BrowserWindow = require('electron').remote;
    // mainWindow = BrowserWindow.getFocusedWindow();
    mainWindow = BrowserWindow.getCurrentWindow();
  }
  // load workflow
  mainWindow.loadURL(`${__dirname}/../wf.html?pid=${prj_id}&pdir=${prj_dir}&wdir=${wkf_dir}&adir=${adp_dir}`);
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
  // get the workflow directory (the most recent). By default, init workflow
  wkf_dir = getWorkflowDir(wkf_dir);
  // get input parameters (from URL)
  let url_params = new URLSearchParams(window.location.search);
  let prj_id = url_params.get('pid');
  let prj_dir = url_params.get('pdir');
  let adp_dir = url_params.get('adir');
  // add workflow workspace
  loadWorkflow(prj_id, prj_dir, wkf_dir, adp_dir);
}

// Import adaptor from folder (sync). By default open the basic adaptor (00_main_input)
function importAdaptor(adp_dir) {
  // get input parameters (from URL)
  let url_params = new URLSearchParams(window.location.search);
  let prj_id = url_params.get('pid');
  let prj_dir = url_params.get('pdir');
  let wkf_dir = url_params.get('wdir');
  // add the absolute path to adaptor folder
  adp_dir = `${process.env.ISANXOT_SRC_HOME}/app/adaptors/${adp_dir}`;
  // add workflow workspace
  loadWorkflow(prj_id, prj_dir, wkf_dir, adp_dir);
}


/*
 * Export functions
 */

module.exports = {
  samplesWkfDir: samplesWkfDir,
  getWorkflowCfg: getWorkflowCfg,
  getWorkflowDir: getWorkflowDir,
  getAdaptorDir: getAdaptorDir,
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
