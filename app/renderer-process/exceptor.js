let remote = require('electron').remote; 
let dialog = remote.dialog; 

function showMessageBox(head, message, end=false) {
  dialog.showErrorBox(head, message);
  if ( end ) {
    
  }
};

// We assign properties to the `module.exports` property, or reassign `module.exports` it to something totally different.
// In  the end of the day, calls to `require` returns exactly what `module.exports` is set to.
module.exports.showMessageBox = showMessageBox;
