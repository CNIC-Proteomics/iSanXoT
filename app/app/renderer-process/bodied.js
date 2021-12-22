/*
 * Import libraries
 */

let fs = require('fs');
let path = require('path');
// let remote = require('electron').remote;

let exceptor = require('./exceptor');
var importer = module.parent.exports; // avoiding circular dependencies with Node require()
let commoner = require('./common');
let ehandler = require('./ehandler');
// let sessioner = require('./sessioner');

/*
 * Import variables and Variables
 */

// get imported variables
let prj_dir = importer.prj_dir;
let wkf_dir  = importer.wkf_dir;
let prj_cfg  = importer.prj_cfg;
let wf  = importer.wf;

// get env variables
let adpDir = process.env.ISANXOT_ADAPTOR_HOME;

/*
 * Local functions
 */

// create hash report of commands from a file
function extract_tasktable_info(cmd, itbl) {
  // Extract the info from tables
  let tbl = {};
  let order = 1;
  let id = null;
  let cols_empty = [];
  for (var i = 0; i < itbl.length; i++) {
    let l = itbl[i];
    if ( l && l.length > 0 && l != '' && l !== undefined && !(commoner.allBlanks(l))) {
      // add the header of table
      if ( i === 0 ) {
        let cols = itbl[i+1];
        // get all indexes of empty elements
        // remove all empty elements in column headers
        cols_empty = commoner.getAllIndexes(l,"");
        cols = commoner.removeListIndexes(l, cols_empty);
        // save
        tbl = {
          'cols': cols,
          'table': []
        }
      }
      // add the data of table
      else {
        // remove all empty elements of header in the data
        if (cols_empty.length > 0) {
          l = commoner.removeListIndexes(l, cols_empty);
        }
        // save line
        tbl['table'].push(l);
      }
    }
  }
  // Get only the tasktable for the given cmd
  // Extract the info for the tasktable ONLY when the columns between the 'workflow' and the external table are equal
  let tt_cmd = {};
  let cmd_id = cmd['id'];
  let cmd_cols = cmd['tasktable']['params'].map(a => a.id);
  let cmd_header = cmd['tasktable']['params'].map(a => a.name);
  // check if the column names are equal
  if ( commoner.isEqual(cmd_cols, tbl['cols']) ) {
    tt_cmd['data'] = tbl['table'];
    tt_cmd['header'] = cmd_header;
  }
  return tt_cmd;
};

// return empty task-table
function return_empty_tttable(cmd_ttable) {
  let cmd_header = cmd_ttable['params'].map(a => a.name);
  let ttable = {
    'header': cmd_header,
    'data': []
  };
  return ttable;
};


/*
 * Main
 */

// Add the body info with the workflow structure ---
for (var i = 0; i < wf['works'].length; i++) {
  // get variables
  let wk = wf['works'][i];
  let wk_id = wk['id'];
  let wk_label = wk['label'];
  
  // add the tabs and content
  // add html template of sidebars and content (import html template)
  // add the event collapse/expand to the sidebar
  let active = ( i == 0 ) ? 'active' : '';
  $(`#bodied .nav.nav-tabs`).append(`<li class="nav-item"><a class="nav-link ${active}" id="${wk_id}-tab" name="${wk_id}" data-toggle="tab" href="#${wk_id}" role="tab" aria-controls="${wk_id}">${wk_label}</a></li>`);
  
  $(`#bodied .tab-content.main`).append(`<div class="tab-pane ${active}" id="${wk_id}" role="tabpanel" aria-labelledby="${wk_id}-tab"></div>`);
  importer.importHTMLtemplate(`${__dirname}/../sections/page.html`, `#bodied #${wk_id}`);


  // Iterate over all commands
  // create html sidebar and the tasktable
  for (var j = 0; j < wk['cmds'].length; j++) {
    let cmd = wk['cmds'][j];
    let cmd_id = cmd['id'];
    let cmd_label = cmd['label'];
    let cmd_title = cmd['title'];

    // create html sidebar
    if ( cmd['visible'] ) { // If the command is not visible, we don't show the sidebar menu
      $(`#${wk_id} #sidebar .cmds`).append(`<li><a id="${cmd_id}" title="${cmd_title}">${cmd_label}</a></li>`);
    }
    // create main div for the tasktable frames
    $(`#${wk_id} #page-content`).append(`<div id="page-tasktable-${cmd_id}"></div>`);
    // add create tasktable panel
    if ( 'panel_adp' in cmd && cmd['panel_adp'] ) {
      importer.importHTMLtemplate(path.join(adpDir, cmd['panel_adp']), `#${wk_id} #page-tasktable-${cmd_id}`);
    } else if ( 'panel' in cmd && cmd['panel'] ) {
      importer.importHTMLtemplate(`${__dirname}/../${cmd['panel']}`, `#${wk_id} #page-tasktable-${cmd_id}`);
    }
    // add the help modal of the tasktable/command
    if ( 'help_adp' in cmd && cmd['help_adp'] ) {
      importer.importHTMLtemplate(path.join(adpDir, cmd['help_adp']), `#${wk_id} #page-tasktable-${cmd_id} .help_adp`);
    } else if ( 'help_modal' in cmd && cmd['help_modal'] ) {
      importer.importHTMLtemplate(`${__dirname}/../${cmd['help_modal']}`, `#${wk_id} #page-tasktable-${cmd_id} .help_modal`);
    }
    // add the short description
    $(`#${wk_id} #page-tasktable-${cmd_id} .sdesc p`).html(cmd['sdesc']);

    // Extract the task-table of command ---
    if ( 'tasktable' in cmd && cmd['visible'] ) {
      let cmd_ttable = cmd['tasktable'];

      let ttable_file = `${wkf_dir}/${cmd_ttable['file']}`;
      let ttable = {};
      if ( ttable_file !== undefined && fs.existsSync(`${ttable_file}`) ) {
        let ttable_raw = [];
        try {
        // Split the lines and tabular lines
        // Then, for each cell, it replaces the "{2,} and " at the begining and the end.
        // convert command file into a dictionary
          let s = fs.readFileSync(`${ttable_file}`).toString();
          ttable_raw = s.split('\n').map( row => row.split('\t').map(r => r.replace(/^["']\s*(.*)\s*["']\s*\n*$/mg, '$1').trim().replace(/"{2,}/g,'"')) )
          if ( !ttable_raw || ttable_raw === undefined || ttable.length === 0 ) {
            exceptor.showErrorMessageBox('Error Message', `Reading the task-table file: ${ttable_file}`, end=false);
            ttable = return_empty_tttable(cmd_ttable);
          }
        } catch (ex) {
          exceptor.showErrorMessageBox('Error Message', `Reading the task-table: ${ttable_file}`, end=false);
          ttable = return_empty_tttable(cmd_ttable);
        }
        try {
          ttable = extract_tasktable_info(cmd, ttable_raw);
          if ( !ttable || ttable === undefined || Object.keys(ttable).length === 0 ) {
            exceptor.showErrorMessageBox('Error Message', `Extracting the data of task-table: ${ttable_file}`, end=false);
            ttable = return_empty_tttable(cmd_ttable);
          }
        } catch (ex) {
          exceptor.showErrorMessageBox('Error Message', `Extracting the data of task-table: ${ttable_file}`, end=false);
          ttable = return_empty_tttable(cmd_ttable);
        }
      }
      else {
        // create empty table
        ttable = return_empty_tttable(cmd_ttable);
      }

      // if the data table is empty or not
      if (!ttable['data'] || ttable['data'].length == 0) {
        ttable['data'] = [[]]; // init the data table
      }
      else {
        // update the sidebar
        $(`#sidebar #${cmd_id}`).text(`${cmd_label}*`);
      }
            
      // get the index of optional parameters
      let cmd_params_opt_index = commoner.getIndexParamsWithAttr(cmd_ttable['params'], 'type', 'optional');

      // get the index of Columns with readOnly parameter
      let cmd_params_readonlycol_index = commoner.getIndexParamsWithAttr(cmd_ttable['params'], 'readOnly', true);

      // get the index of DropDown parameters
      let [cmd_params_hottable_index, cmd_params_hottable] = commoner.getIndexParamsWithKey(cmd_ttable['params'], 'hottable');

      // get the index of select parameters
      let [cmd_params_select_index, cmd_params_select] = commoner.getIndexParamsWithKey(cmd_ttable['params'], 'select');
      
      // get the index of dropdown parameters
      let [cmd_params_dropdown_index, cmd_params_dropdown] = commoner.getIndexParamsWithKey(cmd_ttable['params'], 'dropdown');

      // get the index of checkbox parameters
      let [cmd_params_checkbox_index, cmd_params_checkbox] = commoner.getIndexParamsWithKey(cmd_ttable['params'], 'checkbox');

      // create html tasktable
      $(`#${wk_id} #page-tasktable-${cmd_id}`).append(`<div name="hot" class="tasktable hot handsontable htRowHeaders htColumnHeaders"></div>`);
      $(`#${wk_id} #page-tasktable-${cmd_id} .tasktable`).handsontable({
          data: ttable['data'],
          width: '100%',
          height: 'auto',
          rowHeights: 23,
          rowHeaders: true,
          colHeaders: ttable['header'],
          minRows: 2,
          minCols: ttable['header'].length,
          maxCols: ttable['header'].length,
          minSpareRows: 1,
          contextMenu: true,
          manualColumnResize: true,
          autoColumnSize: true,
          hiddenColumns: {
            'columns': cmd_params_opt_index,
            'indicators': false
          },
          cells: function (row, col) {
            var cellProperties = {};
            // readOnly column (coming from the wortkflow.json config file)
            if (cmd_params_readonlycol_index && cmd_params_readonlycol_index.length > 0 && cmd_params_readonlycol_index.includes(col)) {
              cellProperties.readOnly = true;
            }
            // column with handsontables inside (coming from the wortkflow.json config file)
            if (cmd_params_hottable_index && cmd_params_hottable_index.length > 0 && cmd_params_hottable_index.includes(col)) {
              let hottable_header = cmd_params_hottable[col].header;
              let hottable_data = [];
              for ( k in cmd_params_hottable[col].data) {
                hottable_data.push( [ k, cmd_params_hottable[col].data[k] ] );
              }
              this.type = 'handsontable';
              this.handsontable = {
                colHeaders: hottable_header,
                autoColumnSize: true,
                data: hottable_data,
                getValue: function() {
                  var selection = this.getSelectedLast();
                  return this.getSourceDataAtRow(selection[0])[0]; // return the first column
                },
              };
            }
            // column with handsontables inside (coming from the wortkflow.json config file)
            if (cmd_params_select_index && cmd_params_select_index.length > 0 && cmd_params_select_index.includes(col)) {
              this.editor = 'select';
              this.selectOptions = cmd_params_select[col];
            }
            // column with dropdown inside (coming from the wortkflow.json config file)
            if (cmd_params_dropdown_index && cmd_params_dropdown_index.length > 0 && cmd_params_dropdown_index.includes(col)) {
              this.source = cmd_params_dropdown[col];
              this.type = "autocomplete";
              this.strict = false;
              // this.filter = true;
              this.visibleRows = 10;
              this.trimDropdown = false;
            }
            // column with checkbox inside (coming from the wortkflow.json config file)
            if (cmd_params_checkbox_index && cmd_params_checkbox_index.length > 0 && cmd_params_checkbox_index.includes(col)) {
              this.type = "checkbox";
              this.checkedTemplate = 1;
              this.uncheckedTemplate = "";
            }
            return cellProperties;
          },
          licenseKey: 'non-commercial-and-evaluation'    
      });

    } // end tasktable in cmd

  } // end loop of commands


  /* Init the Work tab */

  // display the first command
  $(`#${wk_id} #sidebar .cmds a:first`).addClass("active");
  // add the title of first command (with the identifier)
  let init_cmd_id = $(`#${wk_id} #sidebar .cmds a:first`).attr('id');
  let init_cmd_title = $(`#${wk_id} #sidebar .cmds a:first`).attr('title');
  $(`#${wk_id} #page .page-header`).html(init_cmd_title);
  $(`#${wk_id} #page .page-header`).attr('name', init_cmd_id);
  // hide all tables except the first
  $(`#${wk_id} div[id^=page-tasktable-]:not(:first)`).hide();


  /* Events for the Work tab */

  // render the tables each time we click on work tabs
  $(`a[id="${wk_id}-tab"]`).on('shown.bs.tab', function (e) {
    // hide all tables
    // displays the last table shown (in the title)
    // render the table
    $(`#${wk_id} div[id^=page-tasktable-]`).hide();
    let cmd_id = $(`#${wk_id} #page .page-header`).attr('name');
    $(`#${wk_id} #page-tasktable-${cmd_id}`).show();
    $(`#${wk_id} #page-tasktable-${cmd_id} .tasktable`).handsontable('render');
  });

  // events for the sidebar menu
  $(`#${wk_id} #sidebar .cmds a`).click(function (event) {
    event.preventDefault();
    // highlight the sidebar menu
    $(`#${wk_id} #sidebar .cmds a`).removeClass("active");
    $(this).addClass("active");
    // get the command info
    let cmd_id = $(this).attr('id');
    let cmd_title = $(this).attr('title');
    // show title of command
    $(`#${wk_id} #page .page-header`).html(cmd_title);
    $(`#${wk_id} #page .page-header`).attr('name', cmd_id);
    // hide all tables
    // show the current command table
    // render the table
    $(`#${wk_id} div[id^=page-tasktable-]`).hide();
    $(`#${wk_id} #page-tasktable-${cmd_id}`).show();
    $(`#${wk_id} #page-tasktable-${cmd_id} .tasktable`).handsontable('render');
  });

} // end loop of works (tabs)

// Add title to workflow ---
$(`#bodied h3.text-center`).html(`${wf['label']}`);
$(`#bodied h3.text-center`).attr('name', `${wf['id']}`);

// Add information from loading proyect ---
if ( prj_dir && prj_dir != '') {
  $(`#__OUTDIR__ input`).val(`${prj_dir}`);
}
if ( prj_cfg ) {
  // add number of threads
  if ( "ncpu" in prj_cfg ) $('#nthreads').val(prj_cfg["ncpu"]);

  // add values of all paneladaptors
  $(`[id^=paneladaptor-]`).find(".adaptor_inputs").each(function(){
    if ( 'adaptor_inputs' in prj_cfg && this.id in prj_cfg['adaptor_inputs'] ) {
      let v = prj_cfg['adaptor_inputs'][this.id];
      $(this).find("input").val(`${v}`);
    }
  });
}


// Save the project info into the session storage
// sessioner.addProjectToSession(odir);




/*
 * Activate the events
 */

// Active the advanced options if apply
ehandler.activeAdvancedEvents(importer);
