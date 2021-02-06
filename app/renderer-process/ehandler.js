/*
 * Import libraries
 */

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


  $(`#${wk_id} #page-tasktable-${cmd_id} .modal`).modal();

}

/*
 * Export modules
 */

// Exporting modules
module.exports = {
  openHelpModal:            openHelpModal,
};
