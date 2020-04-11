/*
  Global variables
*/
const { ipcRenderer } = require('electron');
let remote = require('electron').remote;
let dialog = remote.dialog;

function loadingWorkflow() {
  $(`#loader`).show();
  $(document.body).css({'cursor' : 'wait'});
  $(`#main`).css({'opacity' : 0.5});
  $(`#executor`).css({'opacity' : 0.5});
}

function stopLoadingWorkflow() {
  $(`#loader`).hide();
  $(document.body).css({'cursor' : 'default'});
  $(`#main`).css({'opacity' : 1});
  $(`#executor`).css({'opacity' : 1});
}

function showErrorMessageBox(head, message, end=false, page=undefined) {
  stopLoadingWorkflow();
  dialog.showErrorBox(head, message);
  if (page) ipcRenderer.send('load-page', page);
  if (end) throw new Error(message);
};

// Exporting modules
module.exports = {
  loadingWorkflow:     loadingWorkflow,
  stopLoadingWorkflow: stopLoadingWorkflow,
  showErrorMessageBox: showErrorMessageBox,
};
