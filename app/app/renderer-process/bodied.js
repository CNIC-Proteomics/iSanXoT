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
let clipboardCache = importer.clipboardCache;
let sheetclip = importer.sheetclip;

// get env variables
let adpDir = process.env.ISANXOT_ADAPTOR_HOME;

/*
 * Local functions
 */

// create hash report of commands from a file
function extract_tasktable_info(cmd, itbl) {
  // Extract the info from tables
  let tbl = {};
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
  let cmd_cols = cmd['params'].map(a => a.id);
  let cmd_header = cmd['params'].map(a => a.name);
  // check if the column names are equal
  if ( commoner.isEqual(cmd_cols, tbl['cols']) ) {
    tt_cmd['data'] = tbl['table'];
    tt_cmd['header'] = cmd_header;
  }
  return tt_cmd;
};

// return empty task-table
function return_empty_tttable(ttable) {
  let cmd_header = ttable['params'].map(a => a.name);
  let ttable_data = {
    'header': cmd_header,
    'data': []
  };
  return ttable_data;
};


/*
 * Main
 */

// Add the body info with the workflow structure ---
for (var h = 0; h < wf['tabs'].length; h++) { // go through tabs
  // get variables
  let tab = wf['tabs'][h];
  let tab_id = tab['id'];
  let tab_label = tab['label'];
  let tab_visible = ( 'visible' in tab ) ? tab['visible'] : true;
  if ( tab_visible ) {  

    // add the tabs and content
    // active the first tab content
    let active = ( h == 0 ) ? 'active' : '';
    $(`#bodied .nav.nav-tabs`).append(`<li class="nav-item"><a class="nav-link ${active}" id="${tab_id}-tab" name="${tab_id}" data-toggle="tab" href="#${tab_id}" role="tab" aria-controls="${tab_id}">${tab_label}</a></li>`);

    // add html template of sidebars and content (import html template)
    // add the event collapse/expand to the sidebar
    $(`#bodied .tab-content.main`).append(`<div class="tab-pane ${active}" id="${tab_id}" role="tabpanel" aria-labelledby="${tab_id}-tab"></div>`);
    importer.importHTMLtemplate(`${__dirname}/../sections/page.html`, `#bodied #${tab_id}`);

    // create html page for...
    for (var i = 0; i < tab['works'].length; i++) { // go through works
      // get variables
      let wk = tab['works'][i];
      let wk_id = wk['id'];
      let wk_label = wk['label'];
      let wk_title = wk['title'];
      let wk_visible = ( 'visible' in wk ) ? wk['visible'] : false;

      // create html sidebar
      // create main div for the tasktable frames
      // If the command is not visible, we don't show the sidebar menu
      if ( wk_visible && wk_label && wk_title ) {
        $(`#${tab_id} #sidebar .works`).append(`<li><a id="${wk_id}" title="${wk_title}">${wk_label}</a></li>`);
        $(`#${tab_id} #page-content`).append(`<div id="page-work-${wk_id}"></div>`);
      }
      // add create tasktable panel
      if ( tab_id == 'inputs' && 'panel' in wk ) {
        importer.importHTMLtemplate(path.join(adpDir, wk['panel']), `#page-work-${wk_id}`);
      } else if ( 'panel' in wk ) {
        importer.importHTMLtemplate(`${__dirname}/../${wk['panel']}`, `#page-work-${wk_id}`);
      }
      // add the help modal of the tasktable/command
      if ( tab_id == 'inputs' && 'hmodal' in wk ) {
        importer.importHTMLtemplate(path.join(adpDir, wk['hmodal']), `#page-work-${wk_id} .help_modal`);
      } else if ( 'hmodal' in wk ) {
        importer.importHTMLtemplate(`${__dirname}/../${wk['hmodal']}`, `#page-work-${wk_id} .help_modal`);
      }
      // add the short description
      $(`#page-work-${wk_id} .sdesc p`).html(wk['sdesc']);

      // create html page for...
      for (var j = 0; j < wk['cmds'].length; j++) { // go through cmds
        let cmd = wk['cmds'][j];
        let cmd_id = cmd['id'];

        // create html page
        if ( $(`#page-work-${wk_id} #page-cmd-${cmd_id}`).length == 0 ) $(`#page-work-${wk_id}`).append(`<div id="page-cmd-${cmd_id}"></div>`);

        // extract the task-table if it has params!!
        if ( 'tasktable' in cmd && commoner.checkAttrInListObj(cmd['tasktable'], 'params') ) {
          // create html page for...
          for (let k=0; k < cmd['tasktable'].length; k++) { // go through ttables
            let ttable = cmd['tasktable'][k];
            let ttable_id = ttable['id'];
            let ttable_file = `${wkf_dir}/${ttable['file']}`;

            // create html page if not apply
            if ( $(`#page-cmd-${cmd_id} #page-ttable-${ttable_id}`).length == 0 ) $(`#page-cmd-${cmd_id} `).append(`<div id="page-ttable-${ttable_id}"></div>`);

            // get task-table data
            let ttable_data = {};          
            if ( ttable_file !== undefined && fs.existsSync(`${ttable_file}`) ) {
              let ttable_raw = [];
              try {
              // Split the lines and tabular lines
              // Then, for each cell, it replaces the "{2,} and " at the begining and the end.
              // convert command file into a dictionary
                let s = fs.readFileSync(`${ttable_file}`).toString();
                ttable_raw = s.split('\n').map( row => row.split('\t').map(r => r.replace(/^["']\s*(.*)\s*["']\s*\n*$/mg, '$1').trim().replace(/"{2,}/g,'"')) )
                if ( !ttable_raw || ttable_raw === undefined || ttable_data.length === 0 ) {
                  exceptor.showErrorMessageBox('Error Message', `Reading the task-table file: ${ttable_file}`, end=false);
                  ttable_data = return_empty_tttable(ttable);
                }
              } catch (ex) {
                exceptor.showErrorMessageBox('Error Message', `Reading the task-table: ${ttable_file}`, end=false);
                ttable_data = return_empty_tttable(ttable);
              }
              try {
                ttable_data = extract_tasktable_info(ttable, ttable_raw);
                if ( !ttable_data || ttable_data === undefined || Object.keys(ttable_data).length === 0 ) {
                  exceptor.showErrorMessageBox('Error Message', `Extracting the data of task-table: ${ttable_file}`, end=false);
                  ttable_data = return_empty_tttable(ttable);
                }
              } catch (ex) {
                exceptor.showErrorMessageBox('Error Message', `Extracting the data of task-table: ${ttable_file}`, end=false);
                ttable_data = return_empty_tttable(ttable);
              }
            }
            else {
              // create empty table
              ttable_data = return_empty_tttable(ttable);
            }

            // if the data table is empty or not
            if (!ttable_data['data'] || ttable_data['data'].length == 0) {
              ttable_data['data'] = [[]]; // init the data table
            }
            else {
              // update the sidebar
              $(`#sidebar #${wk_id}`).text(`${wk_label}*`);
            }
                  
            // get the index of optional parameters
            let cmd_params_opt_index = commoner.getIndexParamsWithAttr(ttable['params'], 'type', 'optional');

            // get the index of Columns with readOnly parameter
            let cmd_params_readonlycol_index = commoner.getIndexParamsWithAttr(ttable['params'], 'readOnly', true);

            // // get the index of DropDown parameters
            // let [cmd_params_hottable_index, cmd_params_hottable] = commoner.getIndexParamsWithKey(ttable['params'], 'hottable');

            // get the index of select parameters
            let [cmd_params_select_index, cmd_params_select] = commoner.getIndexParamsWithKey(ttable['params'], 'select');
            
            // get the index of dropdown parameters
            let [cmd_params_dropdown_index, cmd_params_dropdown] = commoner.getIndexParamsWithKey(ttable['params'], 'dropdown');

            // get the index of checkbox parameters
            let [cmd_params_checkbox_index, cmd_params_checkbox] = commoner.getIndexParamsWithKey(ttable['params'], 'checkbox');

            // create html optional button
            if ( cmd_params_opt_index && cmd_params_opt_index.length > 0 ) {
              $(`#page-cmd-${cmd_id} #page-ttable-${ttable_id}`).append(`<input class="toggleadv" type="checkbox" data-toggle="toggle" data-on="Show advanced options" data-off="Hide advanced options" data-onstyle="light" data-offstyle="dark" data-width="150px" data-height="30px" data-size="sm" checked></input>`);
            }

            // create html tasktable based on the id
            $(`#page-cmd-${cmd_id} #page-ttable-${ttable_id}`).append(`<div name="hot" class="tasktable hot handsontable htRowHeaders htColumnHeaders"></div>`);
            $(`#page-cmd-${cmd_id} #page-ttable-${ttable_id} .tasktable`).handsontable({
                data: ttable_data['data'],
                width: 'auto',
                height: 'auto',
                rowHeights: 23,
                rowHeaders: true,
                colHeaders: ttable_data['header'],
                minRows: 2,
                minCols: ttable_data['header'].length,
                maxCols: ttable_data['header'].length,
                minSpareRows: 1,
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
                  // // column with handsontables inside (coming from the wortkflow.json config file)
                  // if (cmd_params_hottable_index && cmd_params_hottable_index.length > 0 && cmd_params_hottable_index.includes(col)) {
                  //   let hottable_header = cmd_params_hottable[col].header;
                  //   let hottable_data = [];
                  //   for ( k in cmd_params_hottable[col].data) {
                  //     hottable_data.push( [ k, cmd_params_hottable[col].data[k] ] );
                  //   }
                  //   this.type = 'handsontable';
                  //   this.handsontable = {
                  //     colHeaders: hottable_header,
                  //     autoColumnSize: true,
                  //     data: hottable_data,
                  //     getValue: function() {
                  //       var selection = this.getSelectedLast();
                  //       return this.getSourceDataAtRow(selection[0])[0]; // return the first column
                  //     },
                  //   };
                  // }
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
            // add handsontable settings
            if ( 'settings' in ttable ) {
              $(`#page-cmd-${cmd_id} #page-ttable-${ttable_id} .tasktable`).handsontable('updateSettings', ttable['settings'] );
              $(`#page-cmd-${cmd_id} #page-ttable-${ttable_id} .tasktable`).handsontable('render');
            }
            // update the context menu
            $(`#page-cmd-${cmd_id} #page-ttable-${ttable_id} .tasktable`).handsontable('updateSettings', {
              afterCopy: function(changes) { clipboardCache = sheetclip.stringify(changes); },
              afterCut: function(changes) { clipboardCache = sheetclip.stringify(changes); },
              // we want to be sure that our cache is up to date, even if someone pastes data from another source than our tables.
              afterPaste: function(changes) { clipboardCache = sheetclip.stringify(changes); },
              contextMenu: ['undo','redo','make_read_only','---------','copy','cut',
                {
                  key: 'paste',
                  name: 'Paste',
                  disabled: function() {
                    return clipboardCache.length === 0;
                  },
                  callback: function() {
                    var plugin = this.getPlugin('copyPaste');
          
                    this.listen();
                    plugin.paste(clipboardCache);
                  }
                }
              ],  
            });
            $(`#page-cmd-${cmd_id} #page-ttable-${ttable_id} .tasktable`).handsontable('render');

          }

        } // end tasktable in cmd
      }
    } // end loop of commands

    /* Init the Work tab */

    // display the first work
    $(`#${tab_id} #sidebar .works a:first`).addClass("active");
    // add the title of first command (with the identifier)
    let init_wk_id = $(`#${tab_id} #sidebar .works a:first`).attr('id');
    let init_wk_title = $(`#${tab_id} #sidebar .works a:first`).attr('title');
    $(`#${tab_id} #page .page-header`).html(init_wk_title);
    $(`#${tab_id} #page .page-header`).attr('name', init_wk_id);
    // hide all tables except the first
    $(`#${tab_id} div[id^=page-work-]:not(:first)`).hide();


    /* Events for the Work tab */

    // render the tables each time we click on work tabs
    $(`a[id="${tab_id}-tab"]`).on('shown.bs.tab', function (e) {
      // hide all tables
      // displays the last table shown (in the title)
      // render alls tables
      $(`#${tab_id} div[id^=page-work-]`).hide();
      let wk_id = $(`#${tab_id} #page .page-header`).attr('name');
      $(`#${tab_id} #page-work-${wk_id}`).show();
      for (let i=0; i<$(`#page-work-${wk_id} .tasktable`).length; i++) {
        let e = $(`#page-work-${wk_id} .tasktable`)[i];
        $(e).handsontable('render');
      }
    });

    // events for the Works sidebar menu
    $(`#${tab_id} #sidebar .works a`).click(function (event) {
      event.preventDefault();
      // highlight the sidebar menu
      $(`#${tab_id} #sidebar .works a`).removeClass("active");
      $(this).addClass("active");
      // get the command info
      let wk_id = $(this).attr('id');
      let wk_title = $(this).attr('title');
      // show title of command
      $(`#${tab_id} #page .page-header`).html(wk_title);
      $(`#${tab_id} #page .page-header`).attr('name', wk_id);
      // hide all tables
      // show the current command table
      // render the table
      $(`div[id^=page-work-]`).hide();
      $(`#page-work-${wk_id}`).show();
      $(`#page-work-${wk_id} .tasktable`).handsontable('render');
    });

  } // end loop of works
} // end for loop of tabs

// Add title to workflow ---
$(`#bodied h3.text-center`).html(`${wf['label']}`);
$(`#bodied h3.text-center`).attr('name', `${wf['id']}`);

// Add information from loading proyect ---
if ( prj_dir && prj_dir != '') {
  $(`#__OUTDIR__`).val(`${prj_dir}`);
}
if ( prj_cfg ) {
  // add number of threads
  if ( "ncpu" in prj_cfg ) $('#nthreads').val(prj_cfg["ncpu"]);
  // add all values for the key element
  if ( 'inpcmds' in prj_cfg ) {
    for ( let i=0; i < prj_cfg['inpcmds'].length; i++ ) {
      if ( 'params' in prj_cfg['inpcmds'][i] ) {
        let params = prj_cfg['inpcmds'][i]['params'];
        for (let j=0; j < params.length; j++) {
          let k = params[j]['key'];
          let v = params[j]['val'];
          $(`#${k}`).val(v);
        }
      }
    }
  }
}


// Save the project info into the session storage
// sessioner.addProjectToSession(odir);




/*
 * Activate the events
 */

// Active the advanced options if apply
ehandler.activeAdvancedEvents(importer);
