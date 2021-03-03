/*
 * Import libraries
 */
let exceptor = require('./exceptor');
let importer = require('./imports');


/*
 * Local functions
 */

// Open Help Modals
function openHelpModal(t) {
  console.log("openHelpModal");
  let t_parent = $(t).parents(`.tab-pane`);
  let wk_id = $(t_parent).attr('id');
  let cmd_id = $(t_parent).find('.page-header').attr('name');
  console.log(`WK_ID: ${wk_id} > CMD: ${cmd_id}`);


  $(`#${wk_id} [id^=page-tasktable-${cmd_id}] .modal`).modal();

}

/*
 *
 * EVENTS-FUNCTIONS: MAIN INPUTS
 * 
 */


// Add values to Main_Inputs panel, if apply
function addValuesMainInputsPanel(remote, importer, exceptor) {
  // Declare variables
  let mainWindow = remote.getCurrentWindow();
  let dialog = remote.dialog;
  let ptype = importer.ptype;
  let pdir = importer.pdir;
  let wf_exec = importer.wf_exec;
  let wk_id = 'main_inputs';
  let cmd_id = 'CREATE_ID';
  
  // check
  if ( wf_exec === undefined ) {
    let errsms = `wf_exec is undefined`;
    console.log(`${errsms}`);
    exceptor.showErrorMessageBox('Error Message', `${errsms}`);
  }
  if (!(wk_id in wf_exec)) {
    let errsms = `'${wk_id}' key is not in wf_exec`;
    console.log(`${errsms}`);
    exceptor.showErrorMessageBox('Error Message', `${errsms}`);
  }
  
  // Add values
  if ( 'samples' == ptype ) {
    $(`#${wk_id} [id^=page-tasktable-${cmd_id}] #indir`).val(`${pdir}/${wf_exec['main_inputs']['indir']}`);
    $(`#${wk_id} [id^=page-tasktable-${cmd_id}] #outdir`).val(`${pdir}/${wf_exec['main_inputs']['outdir']}`);
  }
  else {
    $(`#${wk_id} [id^=page-tasktable-${cmd_id}] #indir`).val(`${wf_exec['main_inputs']['indir']}`);
    $(`#${wk_id} [id^=page-tasktable-${cmd_id}] #outdir`).val(`${wf_exec['main_inputs']['outdir']}`);
  }

  // EVENTS
  // local function for events
  function extractInputDirectoryFile(inputs, errsms) {
    let out = undefined;
    if(inputs === undefined) {
      console.log(`${errsms}: input is undefined`);
      exceptor.showErrorMessageBox('Error Message', `${errsms}`);
    }
    else if (inputs.canceled) {
      console.log(`${errsms}: canceled operation`);
    }
    else if (!('filePaths' in inputs )) {
      console.log(`${errsms}: filePaths does not defined`);
      exceptor.showErrorMessageBox('Error Message', `${errsms}`);
    }
    else {
      if ( inputs['filePaths'].length == 0 ) {
        console.log(`${errsms}: filePaths is empty`);
        exceptor.showErrorMessageBox('Error Message', `${errsms}`);
      }
      else {
        out = inputs['filePaths'][0];
      }
    }
    return out;
  };
  // fill the table with the input files from the given directory
  function fillInputFilesTable(dir) {
    // Imported variables
    let fs = require('fs');

    let files = fs.readdirSync(dir);
    if ( files !== undefined ) {
      for (var i = 0; i < files.length; i++) {
        $(`#${wk_id} [id^=page-tasktable-${cmd_id}] .tasktable`).handsontable('setDataAtCell', i, 0, `${dir}/${files[i]}`);
      }
    }
  };

  // events for the INPUT directory and OUTPUT directory
  $(`#${wk_id} [id^=page-tasktable-${cmd_id}] button.select-indir`).click(function() {
    dialog.showOpenDialog(mainWindow, { properties: ['openDirectory'] }).then((dirs) => {
      let inpt = extractInputDirectoryFile(dirs, `No input directory selected`);
      if ( inpt !== undefined ) {
        $(`#${wk_id} [id^=page-tasktable-${cmd_id}] #indir`).val(`${inpt}`);
        fillInputFilesTable(inpt);
      }      
    });
  });
  $(`#${wk_id} [id^=page-tasktable-${cmd_id}] button.select-outdir`).click(function() {
    dialog.showOpenDialog(mainWindow, { properties: ['openDirectory'] }).then((dirs) => {
      let inpt = extractInputDirectoryFile(dirs, `No output directory selected`);
      if ( inpt !== undefined ) {
        $(`#${wk_id} [id^=page-tasktable-${cmd_id}] #outdir`).val(`${inpt}`);
      }
    });
  });

} // end addValuesMainInputsPanel


// Create object with the Main_Inputs data extracting from the HTML Elements
function createObjFromMainInputsPanel() {
  let rst = {
    'indir':  $(`#panel-main_inputs [id=indir]`).val(),
    'outdir': $(`#panel-main_inputs [id=outdir]`).val(),
  };
  let keys = ['indir','outdir'];
  for (var i = 0; i < keys.length; i++) {
    let k = keys[i];
    let v = $(`#panel-main_inputs [id=${k}]`).val();
    rst[`${k}`] = v;
  }
  return rst;
} // end createObjFromMainInputsPanel


/*
 *
 * EVENTS-FUNCTIONS: ADVANCED-TOOGLE
 * 
 */


// check if some data of advanced options is available
function checkIfAdvancedOptionsExist(importer, exceptor) {
  // declare variables
  let wf = importer.wf;
  // Go through the works of the workflow
  for (var i = 0; i < wf['works'].length; i++) {
    // get variables
    let wk = wf['works'][i];
    let wk_id = wk['id'];
    // Iterate over all commands
    for (var j = 0; j < wk['cmds'].length; j++) {
      // get variables
      let cmd = wk['cmds'][j];
      let cmd_id = cmd['id'];
      // Get the list of optionals parameters
      let opt = importer.getIndexParamsWithAttr(cmd['params'], 'type', 'optional');
      if ( opt ) {
        // provide the event function
        $(`#${wk_id} [id^=page-tasktable-${cmd_id}] .toggleadv`).change(toggleAdvParameters);

        // get cmd table
        let cmd_table = $(`#${wk_id} [id^=page-tasktable-${cmd_id}] .tasktable`).data('handsontable');
        if (cmd_table !== undefined) {
          // Iterate over the data of opt parameteers
          for (var k = 0; k < opt.length; k++) {
            let opt_idx = opt[k];
            // get the data of opt parameters              
            let cmd_data = cmd_table.getDataAtCol(opt_idx);
            if ( cmd_data ) {
              // if there is data
              if ( !(importer.allBlanks(cmd_data)) ) {
                $(`#${wk_id} [id^=page-tasktable-${cmd_id}] .toggleadv`).trigger('click');
                break;
              }
            }
          }
        }
      }
    }
  }
}

function toggleAdvParameters() {
  // declare variables
  let t = this;
  let wf = importer.wf;

  // Get the work id and the command id from the given checkbox element (go through DOM)
  let t_parent = $(t).parents(`.tab-pane`);
  let wk_id = $(t_parent).attr('id');
  let cmd_id = $(t_parent).find('.page-header').attr('name');

  // Get work attributes from the id
  let wk = importer.getObjectFromID(wf['works'], wk_id);
  if ( wf === undefined ) {
    console.log(wk_id);
    exceptor.showErrorMessageBox('Error Message', `Getting the 'works' attributes from the id`, end=true);
  }

  // Get cmd attributes from the id
  let cmd = importer.getObjectFromID(wk['cmds'], cmd_id);
  if ( cmd === undefined ) {
    console.log(cmd_id);
    exceptor.showErrorMessageBox('Error Message', `Getting the 'cmd' attributes from the id`, end=true);
  }

  // Get the list of optionals parameters
  let opt = importer.getIndexParamsWithAttr(cmd['params'], 'type', 'optional');
  if ( opt === undefined ) {
    exceptor.showErrorMessageBox('Error Message', `Getting the 'optional parameters'`, end=true);
  }

  // Show/Hide 'hiddenColumns'
  if ( $(t).prop('checked') ) {
    $(`#${wk_id} [id^=page-tasktable-${cmd_id}] .tasktable`).handsontable('updateSettings',{'hiddenColumns': {'columns': opt, 'indicators': false } });
  }
  else {
    $(`#${wk_id} [id^=page-tasktable-${cmd_id}] .tasktable`).handsontable('updateSettings',{'hiddenColumns': {'columns': [], 'indicators': false } });
  }
}


/*
 *
 * EVENTS-FUNCTIONS: DATABASES
 * 
 */

// Create object with the Databases data extracting from the HTML Elements
function createObjFromDatabasesPanel() {
  // declare variables
  let rst = { };
  let wk_id = 'databases';
  let cmd_id_1 = 'RELS_TABLE_CATDB';
  let cmd_id_2 = 'RELS_TABLE_CATFILE';

  // extract variables...
  // catdb
  let species = $(`#${wk_id} .panel-databases [id='species'] option:selected`);
  let db = $(`#${wk_id} .panel-databases [id='catids'] option:selected`).val();
  // catfile
  let cfile = $(`#${wk_id} .panel-databases [id='catfile']`).val();
  let dfile = $(`#${wk_id} .panel-databases [id='dbfile']`).val();

  // if all variables are defined and not empty, we take the values for that panel
  // we take the category db by default
  if ( species !== undefined && species.length > 0 && db !== undefined && db != '' ) {
    rst['catid'] = db;
    rst['species'] = '';
    rst['catdbs'] = '';
    for (var i = 0; i < species.length; i++) {
      let o = species[i];
      let v1 = $(o).val();
      let v2 = $(o).text().toLowerCase();
      // update species data
      if (rst['species'] != '') { rst['species'] += `,${v1}` } else { rst['species'] += v1 }
      // update category database
      let v = `${process.env.ISANXOT_LIB_HOME}/dbs/${db}/${v2}_${db}_sw-tr.categories.tsv`;
      if (rst['catdbs'] != '') { rst['catdbs'] += `;${v}` } else { rst['catdbs'] += v }
    }
    // unable table of CatDB and disable table of CatFile
    $(`#${wk_id} #page-tasktable-${cmd_id_1} .disabled_tasktable`).toggleClass('disabled_tasktable tasktable');
    $(`#${wk_id} #page-tasktable-${cmd_id_2} .tasktable`).toggleClass('tasktable disabled_tasktable');
  }
  else if ( cfile !== undefined && cfile != '' && dfile !== undefined && dfile != '' ) {
    rst['catfile'] = cfile;
    rst['dbfile'] = dfile;
    // unable table of CatFile and disable table of CatDB
    $(`#${wk_id} #page-tasktable-${cmd_id_2} .disabled_tasktable`).toggleClass('disabled_tasktable tasktable');
    $(`#${wk_id} #page-tasktable-${cmd_id_1} .tasktable`).toggleClass('tasktable disabled_tasktable');
  }
  return rst;
} // end createObjFromDatabasesPanel



/*
 *
 * EVENTS-FUNCTIONS: DATABASES CATDB
 * 
 */

// Add species in the select option
function addSpeciesInSelect(select, catdbs, catid) {
  // clear the select object
  $(select).selectpicker('destroy');
  $(select).find('option').remove().end();
  // get the catdb from id
  let catdb = importer.getObjectFromID(catdbs, catid);
  if ( catdb !== undefined ) {
    // add the species from the catdb
    for (var i = 0; i < catdb['species'].length; i++) {
      let wf_species = catdb['species'][i];
      $(select).append(`<option value="${wf_species['scientific']}">${wf_species['name']}</option>`);
    }
  }
  // refresh the select
  $(select).selectpicker('refresh');
}
// Add values into panel, if apply
function addValuesPanel_CatDB(importer) {
  // declare variables
  let catdbs  = importer.catdbs;
  let wf_exec  = importer.wf_exec;
  let wk_id = 'databases';
  let cmd_id = 'RELS_TABLE_CATDB';
  
  // Init the databases
  $(`#${wk_id} [id^=page-tasktable-${cmd_id}] #catids`).append(`<option value="" >Select database version...</option>`);
  for (var i = 0; i < catdbs.length; i++) {
    let wf_catdbs = catdbs[i];
    $(`#${wk_id} [id^=page-tasktable-${cmd_id}] #catids`).append(`<option value="${wf_catdbs['id']}" >${wf_catdbs['name']}</option>`);
  }

  // Add values
  if ( 'species' in wf_exec['databases'] && 'catid' in wf_exec['databases'] && 'catdbs' in wf_exec['databases'] ) {
    // fill with the catdb id
    let catid = wf_exec['databases']['catid'];
    $(`#${wk_id} [id^=page-tasktable-${cmd_id}] #catids`).val(`${catid}`);
    // fill the select object from the catid
    addSpeciesInSelect(`#${wk_id} [id^=page-tasktable-${cmd_id}] #species`, catdbs, catid);
    // select the given species
    let species = wf_exec['databases']['species'].split(',');
    $(`#${wk_id} [id^=page-tasktable-${cmd_id}] #species`).selectpicker('val', species);
  }
  
  // Hide table
  $(`#${wk_id} [id^=page-tasktable-${cmd_id}] .tasktable`).hide();

  // Add the values of species every time the catdb changes
  $(`#${wk_id} [id^=page-tasktable-${cmd_id}] #catids`).change(function(){
    $("option:selected", this).each(function() {
      // fill the select object from the catid
      let catid = this.value;
      addSpeciesInSelect(`#${wk_id} [id^=page-tasktable-${cmd_id}] #species`, catdbs, catid);
    });
  });

} // end addValuesPanel_CatDB

// Show/Hide table
function toggleTaskTable_CatDB(t) {
  let wk_id = 'databases';
  let cmd_id = 'RELS_TABLE_CATDB';

  if ( $(t).prop('checked') ) {
    $(`#${wk_id} [id^=page-tasktable-${cmd_id}] .tasktable`).hide();
  }
  else {
    $(`#${wk_id} [id^=page-tasktable-${cmd_id}] .tasktable`).show();
    $(`#${wk_id} [id^=page-tasktable-${cmd_id}] .tasktable`).handsontable('render');
  }
}


/*
 *
 * EVENTS-FUNCTIONS: DATABASES CATFILE
 * 
 */


// Add values into panel, if apply
function addValuesPanel_CatFile(remote, importer, exceptor) {
  // declare variables
  let wf_exec  = importer.wf_exec;
  let mainWindow = remote.getCurrentWindow();
  let dialog = remote.dialog;
  let wk_id = 'databases';
  let cmd_id = 'RELS_TABLE_CATFILE';
  
  // Add values
  if ( 'catfile' in wf_exec['databases'] && 'dbfile' in wf_exec['databases']) {
      if ( 'samples' == ptype ) { // library path + category/db FILE
      $(`#${wk_id} [id^=page-tasktable-${cmd_id}] #catfile`).val(`${pdir}/${wf_exec['databases']['catfile']}`);
      $(`#${wk_id} [id^=page-tasktable-${cmd_id}] #dbfile`).val(`${pdir}/${wf_exec['databases']['dbfile']}`);
    }
    else {  // category/db FILE
      $(`#${wk_id} [id^=page-tasktable-${cmd_id}] #catfile`).val(`${wf_exec['databases']['catfile']}`);
      $(`#${wk_id} [id^=page-tasktable-${cmd_id}] #dbfile`).val(`${wf_exec['databases']['dbfile']}`);
    }
  }

  // Hide table
  $(`#${wk_id} [id^=page-tasktable-${cmd_id}] .tasktable`).hide();

  /*
   * Events
   */
  // local function for events
  function extractInputDirectoryFile(inputs, errsms) {
    let out = undefined;
    if(inputs === undefined) {
      console.log(`${errsms}: input is undefined`);
      exceptor.showErrorMessageBox('Error Message', `${errsms}`);
    }
    else if (inputs.canceled) {
      console.log(`${errsms}: canceled operation`);
    }
    else if (!('filePaths' in inputs )) {
      console.log(`${errsms}: filePaths does not defined`);
      exceptor.showErrorMessageBox('Error Message', `${errsms}`);
    }
    else {
      if ( inputs['filePaths'].length == 0 ) {
        console.log(`${errsms}: filePaths is empty`);
        exceptor.showErrorMessageBox('Error Message', `${errsms}`);
      }
      else {
        out = inputs['filePaths'][0];
      }
    }
    return out;
  };
  // events for the DB file and CATegory file BUTTON
  $(`#${wk_id} [id^=page-tasktable-${cmd_id}] button.select-dbfile`).click(function() {
    let opts = {
      properties: ['openFile'],
      filters :[
        {name: 'Database', extensions: ['fasta', 'fa', 'faa', 'txt']},
        {name: 'All Files', extensions: ['*']}
      ]
    };
    dialog.showOpenDialog(mainWindow, opts).then((files) => {
      let inpt = extractInputDirectoryFile(files, `No database file selected`);
      if ( inpt !== undefined ) {
        $(`#${wk_id} [id^=page-tasktable-${cmd_id}] #dbfile`).val(`${inpt}`);
      }
    });
  });
  $(`#${wk_id} [id^=page-tasktable-${cmd_id}] button.select-catfile`).click(function() {
    let opts = {
      properties: ['openFile'],
      filters :[
        {name: 'Category', extensions: ['tsv', 'csv', 'txt']},
        {name: 'All Files', extensions: ['*']}
      ]
    };
    dialog.showOpenDialog(mainWindow, opts).then((files) => {
      let inpt = extractInputDirectoryFile(files, `No category file seleted`);
      if ( inpt !== undefined ) {
        $(`#${wk_id} [id^=page-tasktable-${cmd_id}] #catfile`).val(`${inpt}`);
      }
    });
  });
  
} // end addValuesPanel_CatFile

// Show/Hide table
function toggleTaskTable_CatFile(t) {
  let wk_id = 'databases';
  let cmd_id = 'RELS_TABLE_CATFILE';

  if ( $(t).prop('checked') ) {
    $(`#${wk_id} [id^=page-tasktable-${cmd_id}] .tasktable`).hide();
  }
  else {
    $(`#${wk_id} [id^=page-tasktable-${cmd_id}] .tasktable`).show();
    $(`#${wk_id} [id^=page-tasktable-${cmd_id}] .tasktable`).handsontable('render');
  }
} // end toggleTaskTable_CatFile


/*
 * Export modules
 */

// Exporting modules
module.exports = {
  openHelpModal:                  openHelpModal,
  addValuesMainInputsPanel:       addValuesMainInputsPanel,
  createObjFromMainInputsPanel:   createObjFromMainInputsPanel,
  checkIfAdvancedOptionsExist:    checkIfAdvancedOptionsExist,
  toggleAdvParameters:            toggleAdvParameters,
  addValuesPanel_CatDB:           addValuesPanel_CatDB,
  toggleTaskTable_CatDB:          toggleTaskTable_CatDB,
  addValuesPanel_CatFile:         addValuesPanel_CatFile,
  toggleTaskTable_CatFile:        toggleTaskTable_CatFile,
  createObjFromDatabasesPanel:    createObjFromDatabasesPanel
};
