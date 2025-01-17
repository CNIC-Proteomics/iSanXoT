/*
 * Import libraries
 */
let commoner = require('./common');


// check if some data of advanced options is available
function activeAdvancedEvents(importer) {
  // declare variables
  let wf = importer.wf;
  for (var h = 0; h < wf['tabs'].length; h++) { // go through the tabs
    // get variables
    let tab = wf['tabs'][h];
    for (var i = 0; i < tab['works'].length; i++) { // go through the works
      // get variables
      let wk = tab['works'][i];
      let wk_id = wk['id'];
      // add the event help_modals
      if ('hmodal' in wk) {
        $(`#page-work-${wk_id} .helpadv`).click(openHelpModal);
      }
      for (var j = 0; j < wk['cmds'].length; j++) { // go through the cmds
        // get variables
        let cmd = wk['cmds'][j];
        let cmd_id = cmd['id'];
        // add the toggle_adv_parameters
        if ('tasktable' in cmd) {
          for (let k=0; k < cmd['tasktable'].length; k++) {
            let ttable = cmd['tasktable'][k];
            let ttable_id = ttable['id'];
            // Get the list of optionals parameters
            let opt = commoner.getIndexParamsWithAttr(ttable['params'], 'type', 'optional');
            if ( opt ) {
              // provide the event function
              $(`#page-ttable-${ttable_id} .toggleadv`).change({'opt': opt, 'wk_id': wk_id, 'cmd_id': cmd_id, 'ttable_id': ttable_id}, toggleAdvParameters);
              // get cmd table
              let cmd_table = $(`#page-ttable-${ttable_id} .tasktable`).data('handsontable');
              if (cmd_table !== undefined) {
                // Iterate over the data of opt parameteers
                for (var l = 0; l < opt.length; l++) {
                  let opt_idx = opt[l];
                  // get the data of opt parameters              
                  let cmd_data = cmd_table.getDataAtCol(opt_idx);
                  if ( cmd_data ) {
                    // if there is data
                    if ( !(commoner.allBlanks(cmd_data)) ) {
                      $(`#page-ttable-${ttable_id} .toggleadv`).trigger('click');
                      break;
                    }
                  }
                }
              }
            }
          }
        } // end tasktable in cmd

      }
    }
  }
}

/* EVENTS-FUNCTIONS: HELP MODALS */

// Open Help Modals
function openHelpModal() {
  // declare variables
  let t = this;
  // get the data
  let t_parent = $(t).parents(`div[id^=page-work]`);
  let wk_divid = $(t_parent).attr('id');
  $(`#${wk_divid} .modal`).modal();
}

/* EVENTS-FUNCTIONS: SIMPLE-TOOGLE */

// toggle Advanced parameters
function toggleAdvParameters(event) {
  // declare variables
  let t = this;
  // get the data
  let wk_id = event.data.wk_id;
  let cmd_id = event.data.cmd_id;
  let ttable_id = event.data.ttable_id
  let opt = event.data.opt;
  // Show/Hide 'hiddenColumns'
  if ( $(t).prop('checked') ) { // Hide 'hiddenColumns'
    $(`#page-cmd-${cmd_id} #page-ttable-${ttable_id} .tasktable`).handsontable('updateSettings',{'hiddenColumns': {'columns': opt, 'indicators': false } });
  }
  else { // Show 'hiddenColumns'
    $(`#page-cmd-${cmd_id} #page-ttable-${ttable_id} .tasktable`).handsontable('updateSettings',{'hiddenColumns': {'columns': [], 'indicators': false } });
  }
};


/*
 * Export modules
 */

// Exporting modules
module.exports = {
  openHelpModal:           openHelpModal,
  activeAdvancedEvents:    activeAdvancedEvents,
};
