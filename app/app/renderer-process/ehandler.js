/*
 * Import libraries
 */
let commoner = require('./common');


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
      if ('help_adp' in cmd) {
        $(`#${wk_id} [id^=page-tasktable-${cmd_id}] .helpadv`).click(openHelpModal);
      } else if ('help_modal' in cmd) {
        $(`#${wk_id} [id^=page-tasktable-${cmd_id}] .helpadv`).click(openHelpModal);
      }

      // add the toggle_adv_parameters
      if ('tasktable' in cmd) {
        for (let k=0; k < cmd['tasktable'].length; k++) {
          let cmd_ttable = cmd['tasktable'][k];
          // Get the list of optionals parameters
          let opt = commoner.getIndexParamsWithAttr(cmd_ttable['params'], 'type', 'optional');
          if ( opt ) {
            let ttable_id = `#${wk_id} #page-tasktable-${cmd_id}`;
            if ( 'id' in cmd_ttable ) ttable_id = `#${wk_id} #${cmd_ttable['id']}`;    
            // provide the event function
            $(`${ttable_id} .toggleadv`).change({'opt': opt, 'wk_id': wk_id, 'cmd_id': cmd_id}, toggleAdvParameters);
            // get cmd table
            let cmd_table = $(`${ttable_id} .tasktable`).data('handsontable');
            if (cmd_table !== undefined) {
              // Iterate over the data of opt parameteers
              for (var l = 0; l < opt.length; l++) {
                let opt_idx = opt[l];
                // get the data of opt parameters              
                let cmd_data = cmd_table.getDataAtCol(opt_idx);
                if ( cmd_data ) {
                  // if there is data
                  if ( !(commoner.allBlanks(cmd_data)) ) {
                    $(`${ttable_id} .toggleadv`).trigger('click');
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
 * Export modules
 */

// Exporting modules
module.exports = {
  openHelpModal:           openHelpModal,
  activeAdvancedEvents:    activeAdvancedEvents,
};
