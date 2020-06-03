/*
 * Import libraries
 */
let fs = require('fs');
let exceptor = require('./exceptor');
let importer = require('./imports');

/*
 * Local functions
 */

// Convert workbook to json
function to_json(workbook) {
  var result = {};
  workbook.SheetNames.forEach(function(sheetName) {    
    // Use raw values (true) or formatted strings (false)
    // When header is 1, the default is to generate blank rows. blankrows must be set to false to skip blank rows.
    // When header is not 1, the default is to skip blank rows. blankrows must be true to generate blank rows    
    var roa = XLSX.utils.sheet_to_json(workbook.Sheets[sheetName], {header:1, raw:false} );
    if (roa.length) result[sheetName] = roa;
  });
  return result;
};

/**
 * Sort object properties (only own properties will be sorted).
 * @param {object} obj object to sort properties
 * @param {string|int} sortedBy 1 - sort object properties by specific value.
 * @param {bool} isNumericSort true - sort object properties as numeric value, false - sort as string value.
 * @param {bool} reverse false - reverse sorting.
 * @returns {Array} array of items in [[key,value],[key,value],...] format.
 */
function sortProperties(obj, sortedBy, isNumericSort, reverse) {
  sortedBy = sortedBy || 1; // by default first key
  isNumericSort = isNumericSort || false; // by default text sort
  reverse = reverse || false; // by default no reverse

  var reversed = (reverse) ? -1 : 1;

  var sortable = [];
  for (var key in obj) {
      if (obj.hasOwnProperty(key)) {
          sortable.push([key, obj[key]]);
      }
  }
  if (isNumericSort)
      sortable.sort(function (a, b) {
          return reversed * (a[1][sortedBy] - b[1][sortedBy]);
      });
  else
      sortable.sort(function (a, b) {
          var x = a[1][sortedBy].toLowerCase(),
              y = b[1][sortedBy].toLowerCase();
          return x < y ? reversed * -1 : x > y ? reversed : 0;
      });
  return sortable; // array in format [ [ key1, val1 ], [ key2, val2 ], ... ]
};
// Extract the index of the 'wrofklow.json' headers taking into account the id header of another list
function extract_new_index(array, indexes) {
	let idxs = array.map(function(val, index) {
  	let idx = null;
  	for( let i=0; i<indexes.length; i++) {
			if (indexes[i].id === val) {
      	idx = i;
        break;
      }
    }
    return idx;
	});
	return idxs;
};
// reorder the list of elements from the given list of indexes
function reorder_index(array, indexes) {
	let out = new Array();
  for( let i=0; i<indexes.length; i++) {
  	let idx = indexes[i];
  	if (idx !== null) {
    	out[idx] = array[i];
    }
	}
  return out;
};

// create hash report of commands from a file
function extract_list_cmds(wk, tbl) {
  let cmds = {};
  let order = 1;
  let id = null;
  for (var i = 0; i < tbl.length; i++) {
    let l = tbl[i];
    if ( l && l.length > 0 ) {
      if ( l[0].startsWith('#') ) {
        id = l[0];
        id = id.replace('#','');
        let header = tbl[i+1];
        let attr = (l.length > 1)? l[1] : null;
        cmds[id] = {
          'order': order,
          'attributes': attr,
          'header': header,
          'table': []
        }
        order += 1 // increase the position of commands
        i = i+1; // increase index after header of command
      }
      else {
        cmds[id]['table'].push(l);
      }
    }
  }
  // sort by the attribute 'order'
  cmds = sortProperties(cmds, 'order', true, false);
  // reindex the columns or delate the columns
  // Iterate over all commands
  // create html sidebar and the tasktable
  for (var j = 0; j < cmds.length; j++) {
    // get variables
    // get the attributes of command from the local file (JSON)
    // get the data of table from the external files (TSV)
    let cmd_id = cmds[j][0];
    let cmd = cmds[j][1];
    // let cmd_header = cmd['header'];
    // let cmd_table = cmd['table'];
    // get the header list based on 'workflow.json'
    let wk_cmd_attr = importer.getObjectFromID(wk, cmd_id);
    if ( wk_cmd_attr === undefined ) {
      console.log(cmd_id);
      exceptor.showErrorMessageBox('Error Message', `Getting the 'cmd' attributes from the id`, end=true);
    }
    // get the new index of columns from the 'workflow' config
    let new_indexes = extract_new_index(cmd['header'], wk_cmd_attr['params']);
    // // reorder the index of the header
    // cmd['header'] = reorder_index(cmd['header'], new_indexes);
    // rename the headers
    cmd['header'] = wk_cmd_attr['params'].map(a => a.name);
    // reorder the data of table
    let new_cmd_table = [];
    for (var k = 0; k < cmd['table'].length; k++) {
      let t = reorder_index(cmd['table'][k], new_indexes);
      new_cmd_table.push(t);
    }
    cmd['table'] = new_cmd_table;
  }

  return cmds;  
};

 /*
 * Import varialbles
 */

let wf       = importer.wf;
let wf_id    = importer.wf_id;
let pdir     = importer.pdir;
let pdir_def = importer.pdir_def;
console.log(pdir);


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
  let wk_file = `${pdir}/${wk['file']}`;

  // Extract the table of commands (JSON) from the external file
  // convert command file into a dictionary
  let tbl_cmds = {};
  let cmds = {};
  try {
    if (fs.existsSync(`${wk_file}`)) {
      tbl_cmds = to_json( XLSX.readFile(`${wk_file}`) );
      if ( tbl_cmds ) {
        tbl_cmds = tbl_cmds['Sheet1']
      }
      else {
        console.log(tbl_cmds);
        exceptor.showErrorMessageBox('Error Message', `Extracting the tables of commands`, end=true);
      }
    }
    else { // default table
      wk_file = `${pdir_def}/${wf_id}/${wk['file']}`;
      tbl_cmds = to_json( XLSX.readFile(`${wk_file}`) )['Sheet1'];
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
    let cmd_id = cmds[j][0];
    let cmd = cmds[j][1];
    let cmd_header = cmd['header'];
    let cmd_table = cmd['table'];
    let cmd_attr = importer.getObjectFromID(wk['cmds'], cmd_id);
    if ( cmd_attr === undefined ) {
      console.log(cmd_id);
      exceptor.showErrorMessageBox('Error Message', `Getting the 'cmd' attributes from the id`, end=true);
    }
    let cmd_label = cmd_attr['label'];

    // get the index of optional parameters
    let cmd_params_opt_index = importer.getIndexParamsWithAttr(cmd_attr['params'], 'type', 'optional');

    // get the index of readOnly parameters
    let cmd_params_readonly_index = importer.getIndexParamsWithAttr(cmd_attr['params'], 'readOnly', true);
    
    // get the index of DropDown parameters
    // Example:
    // "cmds": [{
    //   "id": "COMBINE",
    //   "label": "Combine",
    //   "visible": true,
    //   "panel": "panels/advance.html",
    //   "params": [
    //     { "type": "required", "name": "input" },
    //     { "type": "required", "name": "output" },
    //     { "type": "required", "name": "level", "hottable": {
    //       "header": [ "type", "file name"],
    //       "data": {
    //         "peptidesQ": "p2q_outStats.tsv",
    //         "peptides": "p2a_outStats.tsv",
    //         "proteinsC": "q2c_outStats.tsv",
    //         "proteins": "q2a_outStats.tsv",
    //         "categories": "c2a_outStats.tsv"  
    //         }
    //       }
    //     },
    //     { "type": "optional", "name": "more_params" }
    //   ]
    // }
    let [cmd_params_hottable_index, cmd_params_hottable] = importer.getIndexParamsWithKey(cmd_attr['params'], 'hottable');

    // get the index of select parameters
    let [cmd_params_select_index, cmd_params_select] = importer.getIndexParamsWithKey(cmd_attr['params'], 'select');
    



    // Mandatory header is full
    if (  cmd_header && cmd_header.length > 0 ) {
      // create html sidebar
      // If the command is not visible, we don't show the sidebar menu
      if ( cmd_attr['visible'] ) {
        $(`#${wk_id} #sidebar .cmds`).append(`<li><a id="${cmd_id}">${cmd_label}</a></li>`);
      }
      // create main div for the tasktable frames
      $(`#${wk_id} #page-content`).append(`<div id="page-tasktable-${cmd_id}"></div>`);
      // add create tasktable panel
      if ( cmd_attr['panel'] ) {
        importer.importHTMLtemplate(`${__dirname}/../sections/${cmd_attr['panel']}`, `#${wk_id} #page-tasktable-${cmd_id}`);
      }
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
            // readOnly column (coming from the wortkflow.json config file)
            if (cmd_params_readonly_index && cmd_params_readonly_index.length > 0 && cmd_params_readonly_index.includes(col)) {
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
            return cellProperties;
          },
          licenseKey: 'non-commercial-and-evaluation'    
      });
    }
    else {
      console.log(cmd_is);
      exceptor.showErrorMessageBox('Error Message', `Inconsistency of tasktable header`, end=true);
    }
  } // end loop of commands


  /* Init the Work tab */

  // display the first command
  // add the title of first command (with the identifier)
  let init_cmd_id = $(`#${wk_id} #sidebar .cmds a:first`).attr('id');
  let init_cmd_label = $(`#${wk_id} #sidebar .cmds a:first`).text();
  $(`#${wk_id} #page .page-header`).html(init_cmd_label);
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
    let cmd_id = $(this).attr('id');
    let cmd_label = $(this).text();
    // show title of command
    $(`#${wk_id} #page .page-header`).html(cmd_label);
    $(`#${wk_id} #page .page-header`).attr('name', cmd_id);
    // hide all tables
    // show the current command table
    // render the table
    $(`#${wk_id} div[id^=page-tasktable-]`).hide();
    $(`#${wk_id} #page-tasktable-${cmd_id}`).show();
    $(`#${wk_id} #page-tasktable-${cmd_id} .tasktable`).handsontable('render');
  });

} // end loop of works (tabs)


// add values to Main_Inputs panel, if apply
// function in the 'main_inputs' template
addValuesMainInputsPanel();
