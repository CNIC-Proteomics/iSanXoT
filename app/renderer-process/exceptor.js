let remote = require('electron').remote; 
let dialog = remote.dialog; 

function showMessageBox(head, message, end=false) {
  dialog.showErrorBox(head, message);
  if (end) throw new Error(message);
};

function loadingWorkflow() {
  $(`.loading-page`).show();
  $(document.body).css({'cursor' : 'wait'});
  $(`#main`).css({'opacity' : 0.5});
  $(`#executor`).css({'opacity' : 0.5});
}

function stopLoadingWorkflow() {
  $(`.loading-page`).hide();
  $(document.body).css({'cursor' : 'default'});
  $(`#main`).css({'opacity' : 1});
  $(`#executor`).css({'opacity' : 1});
}

// Exporting modules
module.exports = {
  showMessageBox:      showMessageBox,
  loadingWorkflow:     loadingWorkflow,
  stopLoadingWorkflow: stopLoadingWorkflow
};
