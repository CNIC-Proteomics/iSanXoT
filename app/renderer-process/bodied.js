/*
 * Import libraries
 */
let fs = require('fs');
let remote = require('electron').remote;
let exceptor = require('./exceptor');
let importer = require('./imports');
let ehandler = require('./ehandler');

/*
 * Import varialbles
 */

let wf       = importer.wf;
let cdir     = importer.cdir;
console.log(cdir);


/*
 * Local functions
 */

// create hash report of commands from a file
function extract_list_cmds(wk, itbl) {
  // Extract the info from tables
  let tbls = {};
  let order = 1;
  let id = null;
  let cols_empty = [];
  for (var i = 0; i < itbl.length; i++) {
    let l = itbl[i];
    if ( l && l.length > 0 && l != '' && !(importer.allBlanks(l))) {
      if ( l[0] !== undefined && l[0].startsWith('#') ) {
        id = l[0];
        id = id.replace('#','');
        let cols = itbl[i+1];
        // get all indexes of empty elements
        // remove all empty elements in column headers
        cols_empty = importer.getAllIndexes(cols,"");
        cols = importer.removeListIndexes(cols, cols_empty);
        // save
        tbls[id] = {
          'order': order,
          'cols': cols,
          'table': []
        }
        order += 1 // increase the position of commands
        i = i+1; // increase index after header of command
      }
      else {
        // remove all empty elements of header in the data
        if (cols_empty.length > 0) {
          l = importer.removeListIndexes(l, cols_empty);
        }
        // save 
        tbls[id]['table'].push(l);
      }
    }
  }
  // Extract the cmds from 'workflow' file
  let cmds = [];
  for (var i = 0; i < wk.length; i++) {
    let l = wk[i];
    let id = l['id'];
    let cols = [];
    let header = [];
    if ( 'params' in l && l['params'].length > 0) {
      cols = l['params'].map(a => a.id);
      header = l['params'].map(a => a.name);
    }
    cmds.push({
      'id': id,
      'cols': cols,
      'header': header,
      'table': []
    });
  }
  // Iterate over all commands
  // get the attributes of command from the local file (workflow.JSON)
  // get the data of table from the external files (TSV)
  // extract the info for the tasktable ONLY when the columns between the 'workflow' and the external table are equal
  for (var i = 0; i < cmds.length; i++) {
    let cmd = cmds[i];
    let cmd_id = cmd['id'];
    if ( cmd_id in tbls ) {
      let tbl = tbls[cmd_id];
      // check if the column names are equal
      if ( importer.isEqual(cmd['cols'], tbl['cols']) ) {
        cmd['table'] = tbls[cmd_id]['table'];
      }
    }
  }
  return cmds;  
};


/*
 * Main
 */

// Add title to workflow
$(`#bodied h3.text-center`).html(`${wf['label']}`);
$(`#bodied h3.text-center`).attr('name', `${wf['id']}`);


// Go through the works of the workflow
for (var i = 0; i < wf['works'].length; i++) {
  // get variables
  let wk = wf['works'][i];
  let wk_id = wk['id'];
  let wk_label = wk['label'];
  let wk_file = `${cdir}/${wk['file']}`;

  // Extract the table of commands
  // Split the lines and tabular lines
  // Then, for each cell, it replaces the "{2,} and " at the begining and the end.
  // convert command file into a dictionary
  let tbl_cmds = [];
  let cmds = {};
  try {
    if (fs.existsSync(`${wk_file}`)) {
      let s = fs.readFileSync(`${wk_file}`).toString();
      tbl_cmds = s.split('\n').map( row => row.split('\t').map(r => r.replace(/^["']\s*(.*)\s*["']\s*\n*$/mg, '$1').trim().replace(/"{2,}/g,'"')) )
      if ( !tbl_cmds ) {
        console.log(tbl_cmds);
        exceptor.showErrorMessageBox('Error Message', `Extracting the tables of commands`, end=true);
      }
    }
  } catch (ex) {
    console.log(wk_file);
    exceptor.showErrorMessageBox('Error Message', `Extracting the tables of commands from the files`, end=true);
  }
  try {
    cmds = extract_list_cmds(wk['cmds'], tbl_cmds);
  } catch (ex) {
    console.log(wk_file);
    exceptor.showErrorMessageBox('Error Message', `Extracting the tables of commands individually`, end=true);
  }
  
  // add the tabs and content
  // add html template of sidebars and content (import html template)
  // add the event collapse/expand to the sidebar
  let active = ( i == 0 ) ? 'active' : '';
  $(`#bodied .nav.nav-tabs`).append(`<li class="nav-item"><a class="nav-link ${active}" id="${wk_id}-tab" name="${wk_id}" data-toggle="tab" href="#${wk_id}" role="tab" aria-controls="${wk_id}">${wk_label}</a></li>`);
  
  $(`#bodied .tab-content.main`).append(`<div class="tab-pane ${active}" id="${wk_id}" role="tabpanel" aria-labelledby="${wk_id}-tab"></div>`);
  importer.importHTMLtemplate(`${__dirname}/../sections/page.html`, `#bodied #${wk_id}`);


  // Iterate over all commands
  // create html sidebar and the tasktable
  for (var j = 0; j < cmds.length; j++) {
    // get variables
    // get the attributes of command from the local file (JSON)
    // get the data of table from the external files (TSV)
    let cmd = cmds[j];
    let cmd_id = cmd['id'];
    let cmd_header = cmd['header'];
    let cmd_table = cmd['table'];
    let cmd_attr = importer.getObjectFromID(wk['cmds'], cmd_id);
    if ( cmd_attr === undefined ) {
      console.log(cmd_id);
      exceptor.showErrorMessageBox('Error Message', `Getting the 'cmd' attributes from the id`, end=true);
    }
    let cmd_label = cmd_attr['label'];
    let cmd_title = cmd_attr['title'];

    // create html sidebar
    // If the command is not visible, we don't show the sidebar menu
    if ( cmd_attr['visible'] ) {
      $(`#${wk_id} #sidebar .cmds`).append(`<li><a id="${cmd_id}" title="${cmd_title}">${cmd_label}</a></li>`);
    }
    // create main div for the tasktable frames
    $(`#${wk_id} #page-content`).append(`<div id="page-tasktable-${cmd_id}"></div>`);
    // add create tasktable panel
    if ( cmd_attr['panel'] ) {
      importer.importHTMLtemplate(`${__dirname}/../sections/${cmd_attr['panel']}`, `#${wk_id} #page-tasktable-${cmd_id}`);
    }
    // add the help modal of the tasktable/command
    if ( cmd_attr['help_modal'] ) {
      importer.importHTMLtemplate(`${__dirname}/../sections/${cmd_attr['help_modal']}`, `#${wk_id} #page-tasktable-${cmd_id} .help_modal`);
    }

    // Create the tasktable
    if (cmd_header && cmd_header.length > 0 && 'params' in cmd_attr && cmd_attr['params'].length > 0) {

      // get the index of optional parameters
      let cmd_params_opt_index = importer.getIndexParamsWithAttr(cmd_attr['params'], 'type', 'optional');

      // get the index of Columns with readOnly parameter
      let cmd_params_readonlycol_index = importer.getIndexParamsWithAttr(cmd_attr['params'], 'readOnly', true);

      // get the index of Rows with readOnly parameter
      let cmd_params_readonlyrow_index = cmd_attr['readonly_rows'];
      
      // get the index of DropDown parameters
      let [cmd_params_hottable_index, cmd_params_hottable] = importer.getIndexParamsWithKey(cmd_attr['params'], 'hottable');

      // get the index of select parameters
      let [cmd_params_select_index, cmd_params_select] = importer.getIndexParamsWithKey(cmd_attr['params'], 'select');
      
      // get the index of dropdown parameters
      let [cmd_params_dropdown_index, cmd_params_dropdown] = importer.getIndexParamsWithKey(cmd_attr['params'], 'dropdown');

      // get the index of checkbox parameters
      let [cmd_params_checkbox_index, cmd_params_checkbox] = importer.getIndexParamsWithKey(cmd_attr['params'], 'checkbox');

      // create html tasktable
      $(`#${wk_id} #page-tasktable-${cmd_id}`).append(`<div name="hot" class="tasktable hot handsontable htRowHeaders htColumnHeaders"></div>`);
      if (!cmd_table || cmd_table.length == 0) cmd_table = [[]]; // if the data table is empty, we init
      $(`#${wk_id} #page-tasktable-${cmd_id} .tasktable`).handsontable({
          data: cmd_table,
          width: '100%',
          height: 'auto',
          rowHeights: 23,
          rowHeaders: true,
          colHeaders: cmd_header,
          minRows: 2,
          minCols: cmd_header.length,
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
            // readOnly row (coming from the wortkflow.json config file)
            if (cmd_params_readonlyrow_index && cmd_params_readonlyrow_index.length > 0 && cmd_params_readonlyrow_index.includes(row)) {
              cellProperties.readOnly = true;
            }
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
    }
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


/*
 * Activate the events
 */

// add values into panels, if apply
// functions in the corresponding html template
ehandler.addValuesMainInputsPanel(remote, importer, exceptor);
ehandler.addValuesPanelCatDB(importer);

// check if some data of advanced options is available
ehandler.checkIfAdvancedOptionsExist(importer, exceptor);

