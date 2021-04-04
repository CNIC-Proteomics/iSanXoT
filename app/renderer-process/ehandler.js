/*
 * Import libraries
 */
let exceptor = require('./exceptor');
let importer = require('./imports');
let fs = require('fs');


/*
 * Local functions
 */

// Open Help Modals
function openHelpModal(t) {
  let t_parent = $(t).parents(`.tab-pane`);
  let wk_id = $(t_parent).attr('id');
  let cmd_id = $(t_parent).find('.page-header').attr('name');
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
  let wf_exec = importer.wf_exec;
  
  // check
  if ( wf_exec === undefined ) {
    let errsms = `wf_exec is undefined`;
    console.log(`${errsms}`);
    exceptor.showErrorMessageBox('Error Message', `${errsms}`);
  }
  
  // Add values
  if ( 'samples' == ptype ) {
    $(`[id^=main_inputs] #panel-main_inputs`).find(".main_inputs").each(function(){
      $(this).find("input").val(`${process.env.ISANXOT_LIB_HOME}/${ptype}/${wf_exec['main_inputs'][this.id]}`);
    });

  }
  else {
    $(`[id^=main_inputs] #panel-main_inputs`).find(".main_inputs").each(function(){
      $(this).find("input").val(`${wf_exec['main_inputs'][this.id]}`);
    });
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
  // add only files end with...
  function fillInputFilesTable(dir) {
    let files = fs.readdirSync(dir);
    if ( files !== undefined ) {
      let nrow = 0;
      for (var i = 0; i < files.length; i++) {
        if ( files[i].endsWith("PSMs.txt") || files[i].endsWith("result.tsv") || files[i].endsWith(".txt") ) {
          $(`[id^=main_inputs] #panel-main_inputs`).next('.tasktable').handsontable('setDataAtCell', nrow, 0, `${files[i]}`);
          nrow++;
        }
      }
    }
  };

  // events for the inputs
  $('#__MAIN_INPUTS_INDIR__  button').click(function() {
    dialog.showOpenDialog(mainWindow, { properties: ['openDirectory'] }).then((dirs) => {
      let inpt = extractInputDirectoryFile(dirs, `No input directory selected`);
      if ( inpt !== undefined ) {
        $(`#__MAIN_INPUTS_INDIR__ input`).val(`${inpt}`);
        fillInputFilesTable(inpt);
      }      
    });
  });
  $('#__MAIN_INPUTS_OUTDIR__  button').click(function() {
    dialog.showOpenDialog(mainWindow, { properties: ['openDirectory'] }).then((dirs) => {
      let inpt = extractInputDirectoryFile(dirs, `No output directory selected`);
      if ( inpt !== undefined ) {
        $(`#__MAIN_INPUTS_OUTDIR__ input`).val(`${inpt}`);
      }
    });
  });
  $('#__MAIN_INPUTS_PSMFILE__  button').click(function() {
    dialog.showOpenDialog(mainWindow).then((files) => {
      let inpt = extractInputDirectoryFile(files, `No input file selected`);
      if ( inpt !== undefined ) {
        $(`#__MAIN_INPUTS_PSMFILE__ input`).val(`${inpt}`);
      }
    });
  });
  $('#__MAIN_INPUTS_PDMFILE__  button').click(function() {
    dialog.showOpenDialog(mainWindow).then((files) => {
      let inpt = extractInputDirectoryFile(files, `No input file selected`);
      if ( inpt !== undefined ) {
        $(`#__MAIN_INPUTS_PDMFILE__ input`).val(`${inpt}`);
      }
    });
  });

} // end addValuesMainInputsPanel


// Create object with the Main_Inputs data extracting from the HTML Elements
function createObjFromMainInputsPanel() {
  let rst = {};
  $(`[id^=panel-main_inputs]`).find(".main_inputs").each(function() {
    let k = this.id;
    let v = $(this).find("input").val();
    rst[`${k}`] = v;
  });
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
      let opt = ( 'params' in cmd && cmd['params'].length > 0) ? importer.getIndexParamsWithAttr(cmd['params'], 'type', 'optional') : [];
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

  // extract variables...
  // catdb
  let species = $(`#__MAIN_INPUTS_SPECIES__  select  option:selected`);
  let db = $(`#__MAIN_INPUTS_DBID__  select  option:selected`).val();
  // catfile
  let seqfile = $(`#__MAIN_INPUTS_SEQFILE__  input`).val();
  let cfile = $(`#__MAIN_INPUTS_CATFILE__  input`).val();

  // if all variables are defined and not empty, we take the values for that panel
  // we take the category db by default
  if ( species !== undefined && species.length > 0 && db !== undefined && db != '' ) {
    rst['__MAIN_INPUTS_DBID__'] = db;
    rst['__MAIN_INPUTS_SPECIES__'] = '';
    rst['__MAIN_INPUTS_CATDB__'] = '';
    for (var i = 0; i < species.length; i++) {
      let o = species[i];
      let v1 = $(o).val();
      let v2 = $(o).text().toLowerCase();
      // update species data
      if (rst['__MAIN_INPUTS_SPECIES__'] != '') { rst['__MAIN_INPUTS_SPECIES__'] += `,${v1}` } else { rst['__MAIN_INPUTS_SPECIES__'] += v1 }
      // update category database
      let v = `${process.env.ISANXOT_LIB_HOME}/dbs/${db}/${v2}_${db}_sw-tr.categories.tsv`;
      if (rst['__MAIN_INPUTS_CATDB__'] != '') { rst['__MAIN_INPUTS_CATDB__'] += `;${v}` } else { rst['__MAIN_INPUTS_CATDB__'] += v }
    }
    // unable table of CatDB and disable table of CatFile
    $(`#panel-databases-catdb`).next('.disabled_tasktable').toggleClass('disabled_tasktable tasktable');
    $(`#panel-databases-catfile`).next('.tasktable').toggleClass('tasktable disabled_tasktable');

  }
  else if ( cfile !== undefined && cfile != '' && seqfile !== undefined && seqfile != '' ) {
    rst['__MAIN_INPUTS_SEQFILE__'] = seqfile;
    rst['__MAIN_INPUTS_CATFILE__'] = cfile;
    // unable table of CatFile and disable table of CatDB
    $(`#panel-databases-catfile`).next('.disabled_tasktable').toggleClass('disabled_tasktable tasktable');
    $(`#panel-databases-catdb`).next('.tasktable').toggleClass('tasktable disabled_tasktable');
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
  
  // Init the databases
  $(`#__MAIN_INPUTS_DBID__  select`).append(`<option value="" >Select database version...</option>`);
  for (var i = 0; i < catdbs.length; i++) {
    let wf_catdbs = catdbs[i];
    $(`#__MAIN_INPUTS_DBID__  select`).append(`<option value="${wf_catdbs['id']}" >${wf_catdbs['name']}</option>`);
  }

  // Add values
  if ( '__MAIN_INPUTS_SPECIES__' in wf_exec['databases'] && '__MAIN_INPUTS_DBID__' in wf_exec['databases'] ) {
    // fill with the catdb id
    let catid = wf_exec['databases']['__MAIN_INPUTS_DBID__'];
    $(`#__MAIN_INPUTS_DBID__ select`).val(`${catid}`);
    // fill the select object from the catid
    addSpeciesInSelect(`#__MAIN_INPUTS_SPECIES__ select`, catdbs, catid);
    // select the given species
    let species = wf_exec['databases']['__MAIN_INPUTS_SPECIES__'].split(',');
    $(`#__MAIN_INPUTS_SPECIES__ select`).selectpicker('val', species);
  }
  
  // Hide table
  $(`#panel-databases-catdb`).next('.tasktable').hide();

  // Add the values of species every time the catdb changes
  $(`#__MAIN_INPUTS_DBID__  select`).change(function(){
    $("option:selected", this).each(function() {
      // fill the select object from the catid
      let catid = this.value;
      addSpeciesInSelect(`#__MAIN_INPUTS_SPECIES__ select`, catdbs, catid);
    });
  });

} // end addValuesPanel_CatDB

// Show/Hide table
function toggleTaskTable_CatDB(t) {
  if ( $(t).prop('checked') ) {
    $(`#panel-databases-catdb`).next('.tasktable').hide();
  }
  else {
    $(`#panel-databases-catdb`).next('.tasktable').show();
    $(`#panel-databases-catdb`).next('.tasktable').handsontable('render');

  }
} // end toggleTaskTable_CatDB


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
  
  // Add values
  if ( '__MAIN_INPUTS_CATFILE__' in wf_exec['databases'] && '__MAIN_INPUTS_SEQFILE__' in wf_exec['databases']) {
    if ( 'samples' == ptype ) {
      $(`#panel-databases-catfile`).find(".databases").each(function(){
        $(this).find("input").val(`${process.env.ISANXOT_LIB_HOME}/${ptype}/${wf_exec['databases'][this.id]}`);
      });

    }
    else {
      $(`#panel-databases-catfile`).find(".databases").each(function(){
        $(this).find("input").val(`${wf_exec['databases'][this.id]}`);
      });
    }
  }

  // Hide table
  $(`#panel-databases-catfile`).next('.tasktable').hide();

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
  $('#__MAIN_INPUTS_SEQFILE__  button').click(function() {
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
        $(`#__MAIN_INPUTS_SEQFILE__ input`).val(`${inpt}`);
      }
    });
  });
  $('#__MAIN_INPUTS_CATFILE__  button').click(function() {
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
        $(`#__MAIN_INPUTS_CATFILE__ input`).val(`${inpt}`);
      }
    });
  });
  
} // end addValuesPanel_CatFile

// Show/Hide table
function toggleTaskTable_CatFile(t) {
  if ( $(t).prop('checked') ) {
    $(`#panel-databases-catfile`).next('.tasktable').hide();
  }
  else {
    $(`#panel-databases-catfile`).next('.tasktable').show();
    $(`#panel-databases-catfile`).next('.tasktable').handsontable('render');

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
