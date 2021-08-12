/*
 * Import libraries
 */
let exceptor = require('./exceptor');
let commoner = require('./common');
let fs = require('fs');


// check if some data of advanced options is available
function activeAdvancedEvents(importer) {
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

      // add the event help_modals
      if ('help_modal' in cmd) {
        $(`#${wk_id} [id^=page-tasktable-${cmd_id}] .helpadv`).click(openHelpModal);
      }

      // add the toggle_adv_parameters
      if ('tasktable' in cmd) {
        let cmd_ttable = cmd['tasktable'];
        // Get the list of optionals parameters
        let opt = commoner.getIndexParamsWithAttr(cmd_ttable['params'], 'type', 'optional');
        if ( opt ) {
          // provide the event function
          $(`#${wk_id} [id^=page-tasktable-${cmd_id}] .toggleadv`).change({'opt': opt, 'wk_id': wk_id, 'cmd_id': cmd_id}, toggleAdvParameters);
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
                if ( !(commoner.allBlanks(cmd_data)) ) {
                  $(`#${wk_id} [id^=page-tasktable-${cmd_id}] .toggleadv`).trigger('click');
                  break;
                }
              }
            }
          }
        }
      } // end tasktable in cmd

    }
  }
}

/* EVENTS-FUNCTIONS: HELP MODALS */

// Open Help Modals
function openHelpModal() {
  // declare variables
  let t = this;
  // get the data
  let t_parent = $(t).parents(`.tab-pane`);
  let wk_id = $(t_parent).attr('id');
  let cmd_id = $(t_parent).find('.page-header').attr('name');
  $(`#${wk_id} [id^=page-tasktable-${cmd_id}] .modal`).modal();
}

/* EVENTS-FUNCTIONS: SIMPLE-TOOGLE */

// toggle Advanced parameters
function toggleAdvParameters(event) {
  // declare variables
  let t = this;
  // get the data
  let wk_id = event.data.wk_id;
  let cmd_id = event.data.cmd_id;
  let opt = event.data.opt;
  // Show/Hide 'hiddenColumns'
  if ( $(t).prop('checked') ) { // Hide 'hiddenColumns'
    $(`#${wk_id} [id^=page-tasktable-${cmd_id}] .tasktable`).handsontable('updateSettings',{'hiddenColumns': {'columns': opt, 'indicators': false } });
  }
  else { // Show 'hiddenColumns'
    $(`#${wk_id} [id^=page-tasktable-${cmd_id}] .tasktable`).handsontable('updateSettings',{'hiddenColumns': {'columns': [], 'indicators': false } });
  }
};


/*
 *
 * EVENTS-FUNCTIONS: MAIN INPUTS
 * 
 */

// // Add values to Main_Inputs panel, if apply
// function addValuesMainInputsPanel(remote, importer, exceptor) {
//   // Declare variables
//   let mainWindow = remote.getCurrentWindow();
//   let dialog = remote.dialog;
//   let ptype = importer.ptype;
//   let wf_exec = importer.wf_exec;
  
//   // check
//   if ( wf_exec === undefined ) {
//     let errsms = `wf_exec is undefined`;
//     console.log(`${errsms}`);
//     exceptor.showErrorMessageBox('Error Message', `${errsms}`);
//   }
  
//   // Add values
//   if ( 'samples' == ptype ) {
//     $(`#panel-main_inputs`).find(".main_inputs").each(function(){
//       $(this).find("input").val(`${process.env.ISANXOT_LIB_HOME}/${ptype}/${wf_exec['main_inputs'][this.id]}`);
//     });

//   }
//   else {
//     $(`#panel-main_inputs`).find(".main_inputs").each(function(){
//       if ( 'main_inputs' in wf_exec && this.id in wf_exec['main_inputs'] ) {
//         let v = wf_exec['main_inputs'][this.id];
//         $(this).find("input").val(`${v}`);
//       }
//     });
//   }

//   // EVENTS
//   // local function for events
//   function extractInputDirectoryFile(inputs, errsms) {
//     let out = undefined;
//     if(inputs === undefined) {
//       console.log(`${errsms}: input is undefined`);
//       exceptor.showErrorMessageBox('Error Message', `${errsms}`);
//     }
//     else if (inputs.canceled) {
//       console.log(`${errsms}: canceled operation`);
//     }
//     else if (!('filePaths' in inputs )) {
//       console.log(`${errsms}: filePaths does not defined`);
//       exceptor.showErrorMessageBox('Error Message', `${errsms}`);
//     }
//     else {
//       if ( inputs['filePaths'].length == 0 ) {
//         console.log(`${errsms}: filePaths is empty`);
//         exceptor.showErrorMessageBox('Error Message', `${errsms}`);
//       }
//       else {
//         out = inputs['filePaths'][0];
//       }
//     }
//     return out;
//   };
//   // fill the table with the input files from the given directory
//   // add only files end with...
//   function fillInputFilesTable(dir) {
//     let files = fs.readdirSync(dir);
//     if ( files !== undefined ) {
//       let nrow = 0;
//       for (var i = 0; i < files.length; i++) {
//         if ( files[i].endsWith("PSMs.txt") || files[i].endsWith("result.tsv") || files[i].endsWith(".txt") ) {
//           $(`[id^=main_inputs] #panel-main_inputs`).next('.tasktable').handsontable('setDataAtCell', nrow, 0, `${files[i]}`);
//           nrow++;
//         }
//       }
//     }
//   };

//   // events for the inputs
//   $('#__INDIR__  button').click(function() {
//     dialog.showOpenDialog(mainWindow, { properties: ['openDirectory'] }).then((dirs) => {
//       let inpt = extractInputDirectoryFile(dirs, `No input directory selected`);
//       if ( inpt !== undefined ) {
//         $(`#__INDIR__ input`).val(`${inpt}`);
//         fillInputFilesTable(inpt);
//       }      
//     });
//   });
//   $('#__OUTDIR__  button').click(function() {
//     dialog.showOpenDialog(mainWindow, { properties: ['openDirectory'] }).then((dirs) => {
//       let inpt = extractInputDirectoryFile(dirs, `No output directory selected`);
//       if ( inpt !== undefined ) {
//         $(`#__OUTDIR__ input`).val(`${inpt}`);
//       }
//     });
//   });

// } // end addValuesMainInputsPanel



/*
 *
 * EVENTS-FUNCTIONS: DATABASES CATDB
 * 
 */

// // Create object with the Databases data extracting from the HTML Elements
// function createObjFromDatabasesPanel() {
//   // declare variables
//   let rst = { };

//   // extract variables...
//   // catdb
//   let species = $(`#__SPECIES__  select  option:selected`);
//   let db = $(`#__DBID__  select  option:selected`).val();

//   // if all variables are defined and not empty, we take the values for that panel
//   // we take the category db by default
//   if ( species !== undefined && species.length > 0 && db !== undefined && db != '' ) {
//     rst['__DBID__'] = db;
//     rst['__SPECIES__'] = '';
//     rst['__CATDB__'] = '';
//     for (var i = 0; i < species.length; i++) {
//       let o = species[i];
//       let v1 = $(o).val();
//       let v2 = $(o).text().toLowerCase();
//       // update species data
//       if (rst['__SPECIES__'] != '') { rst['__SPECIES__'] += `,${v1}` } else { rst['__SPECIES__'] += v1 }
//       // update category database
//       let v = `${process.env.ISANXOT_LIB_HOME}/dbs/${db}/${v2}_${db}.categories.tsv`;
//       if (rst['__CATDB__'] != '') { rst['__CATDB__'] += `;${v}` } else { rst['__CATDB__'] += v }
//     }
//   }
//   return rst;
// } // end createObjFromDatabasesPanel


// // Add species in the select option
// function addSpeciesInSelect(select, catdbs, catid) {
//   // clear the select object
//   $(select).selectpicker('destroy');
//   $(select).find('option').remove().end();
//   // get the catdb from id
//   let catdb = importer.getObjectFromID(catdbs, catid);
//   if ( catdb !== undefined ) {
//     // add the species from the catdb
//     for (var i = 0; i < catdb['species'].length; i++) {
//       let wf_species = catdb['species'][i];
//       $(select).append(`<option value="${wf_species['scientific']}">${wf_species['name']}</option>`);
//     }
//   }
//   // refresh the select
//   $(select).selectpicker('refresh');
// }

// // Add values into panel, if apply
// function addValuesPanelCatDB(importer) {
//   // declare variables
//   let catdbs  = importer.catdbs;
//   let wf_exec  = importer.wf_exec;
  
//   // Init the databases
//   $(`#__DBID__  select`).append(`<option value="" >Select database version...</option>`);
//   for (var i = 0; i < catdbs.length; i++) {
//     let wf_catdbs = catdbs[i];
//     $(`#__DBID__  select`).append(`<option value="${wf_catdbs['id']}" >${wf_catdbs['name']}</option>`);
//   }

//   // Add values
//   if ( 'main_inputs' in wf_exec && '__SPECIES__' in wf_exec['main_inputs'] && '__DBID__' in wf_exec['main_inputs'] ) {
//     // fill with the catdb id
//     let catid = wf_exec['main_inputs']['__DBID__'];
//     $(`#__DBID__ select`).val(`${catid}`);
//     // fill the select object from the catid
//     addSpeciesInSelect(`#__SPECIES__ select`, catdbs, catid);
//     // select the given species
//     let species = wf_exec['main_inputs']['__SPECIES__'].split(',');
//     $(`#__SPECIES__ select`).selectpicker('val', species);
//   }
  
//   // // Hide table
//   // $(`#panel-databases-catdb`).next('.tasktable').hide();

//   // Add the values of species every time the catdb changes
//   $(`#__DBID__  select`).change(function(){
//     $("option:selected", this).each(function() {
//       // fill the select object from the catid
//       let catid = this.value;
//       addSpeciesInSelect(`#__SPECIES__ select`, catdbs, catid);
//     });
//   });

// } // end addValuesPanelCatDB

// // Show/Hide table
// function toggleTaskTableCatDB(t) {
//   if ( $(t).prop('checked') ) {
//     $(`#panel-databases-catdb`).next('.tasktable').hide();
//   }
//   else {
//     $(`#panel-databases-catdb`).next('.tasktable').show();
//     $(`#panel-databases-catdb`).next('.tasktable').handsontable('render');

//   }
// } // end toggleTaskTableCatDB




/*
 * Export modules
 */

// Exporting modules
module.exports = {
  openHelpModal:           openHelpModal,
  activeAdvancedEvents:    activeAdvancedEvents,
  // addValuesMainInputsPanel:       addValuesMainInputsPanel,
  // addValuesPanelCatDB:            addValuesPanelCatDB,
  // toggleTaskTableCatDB:           toggleTaskTableCatDB,
  // createObjFromDatabasesPanel:    createObjFromDatabasesPanel
};
