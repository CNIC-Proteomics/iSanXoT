// Remove console log in production mode
if (process.env.ISANXOT_MODE == "production") {
    console.log = function() {};
}

// set the local directory
process.env.ISANXOT_SRC_HOME = process.cwd();

/*
 * Import libraries
 */

let fs = require('fs');
let path = require('path');
let exceptor = require('./exceptor');
let executor = undefined;
let wf_date_id = undefined;

const { ipcRenderer } = require('electron');
const { BrowserWindow, dialog } = require('electron').remote
let mainWindow = BrowserWindow.getFocusedWindow();


/*
 * Events
 */

// Resize table from the window size
var resizeId = null;
function doneResizing() {
    let winheight = $(window).height();    
    if ( $('.tab-content').length ) {
        let newheight = winheight - 156;
        $(`.tab-content`).height(newheight);
    }
    if ( $('.tasktable').length ) {
        let newheight = winheight - 260;
        $(`.tasktable`).height(newheight);
        $(`.wtHolder`).height(newheight);        
        $(`#page-tasktable-CREATE_ID .tasktable`).height('auto');
        $(`#page-tasktable-CREATE_ID .wtHolder`).height('auto');
    }
    if ( $('#panel-logger').length ) {
        let newheight = winheight - 156;
        $(`#panel-logger`).height(newheight);
    }
    if ( $('.logtable').length ) {
        let newheight = winheight - 227;
        $(`#workflowlogs .logtable`).height(newheight);
    }
}

// Function when the windows is resize
$(window).resize(function() {
    clearTimeout(resizeId);
    resizeId = setTimeout(doneResizing, 250);
});
// Operations when the html document is ready
$(document).ready(function() {
    // operations in task-tables
    if ( $('.tasktable').length ) {
        // render all task-table
        $(`.tasktable`).handsontable('render');
    }
    if ( $('.logtable').length ) {
        // render all task-table
        $(`.logtable`).handsontable('render');
    }
    // resize panels
    doneResizing();
});


/*
 * Renderer functions
 */

// local function: add the project folder
function addInputsFileDirectoy(inputs, errsms) {
    if(inputs === undefined) {
      console.log(`${errsms}: input is undefined`);
      exceptor.showErrorMessageBox('Error Message', `${errsms}`);
    }
    else if (inputs.canceled) {
      console.log(`${errsms}: canceled operation`);
    }
    else if (!('filePaths' in inputs )) {
      console.log(`${errsms}: filePaths does not defined`);
      exceptor.showErrorMessageBox('Error Message', `${errsms}`);
    }
    else {
      if ( inputs['filePaths'].length == 0 ) {
        console.log(`${errsms}: filePaths is empty`);
        exceptor.showErrorMessageBox('Error Message', `${errsms}`);
      }
      else {
        let file = inputs['filePaths'][0];
        if(!mainWindow) { mainWindow = this.BrowserWindow }; // needed to load the project when comers from processes frontpage
        mainWindow.loadURL(`file://${__dirname}/../wf.html?ptype=load&pdir=${file}`);
      }
    }
  };  
// Load project folder
function openProject() {
    // Select a folder: Asynchronous - using callback
    // Use the main window to be modal
    let opts = { properties: ["openDirectory"] };
    dialog.showOpenDialog(opts).then((dirs) => {
        isOpenLoadProjectDialog = false;
        addInputsFileDirectoy(dirs, `No project folder selected`);
    });
};
// Save project
function saveProject() {
    if ( wf_date_id && wf ) {
        // loading...
        exceptor.loadingWorkflow();
        setTimeout(function() {
            // save project
            let [,,,] = executor.saveProject(wf_date_id, wf);
            // everything was alright
            exceptor.stopLoadingWorkflow();
            exceptor.showMessageBox('info', "Your project has been saved successfully", title='Save project');
        }, 1000); // due the execSync block everything, we have to wait until loading event is finished
    }
    else {
        exceptor.showMessageBox('warning', "You are in the wrong page and you have not created any workflow", title='No project to save');
    }
};

ipcRenderer.on('openProject',  function() {
    openProject();
});
ipcRenderer.on('saveProject', function() {
    saveProject();
});

  
/*
 * Local functions
 */

// Import workflow template
function importHTMLtemplate(wfhref, tid, before) {
    if (!tid) tid = `#${path.basename(wfhref, '.html')}`;
    if ( document.querySelector(`${tid}`) !== null ) {
        let s = fs.readFileSync(wfhref);
        let frag = document.createRange().createContextualFragment(s.toString());
        let template = frag.querySelector('.task-template');
        let clone = document.importNode(template.content, true);
        if ( before ) { document.querySelector(`${tid}`).prepend(clone); } else { document.querySelector(`${tid}`).appendChild(clone); }
    }
};

// Get the most recent execution directory
// the files has to be sorted by name
function getMostRecentDir(dir) {
    var getDirectories = source =>
    fs.readdirSync(source, { withFileTypes: true })
        .filter(dirent => dirent.isDirectory())
        .map(dirent => dirent.name)
        .reverse();
    // the files has to be sorted by name
    // let files = fs.readdirSync(dir).reverse();
    let files = getDirectories(dir);
    return (files.length > 0)? files[0] : undefined;
}  
// Get a string with the local date
function getWFDate() {
    let d = new Date();
    d.setDate(d.getDate());
    Y = d.getFullYear();
    M = ('0' + (d.getMonth()+1)).slice(-2)
    D = ('0' + d.getDate()).slice(-2)
    h = ('0' + d.getHours()).slice(-2)
    m = ('0' + d.getMinutes()).slice(-2);
    s = ('0' + d.getSeconds()).slice(-2);
    return Y+M+D+h+m+s;
}
// Get the id of current Workflow extracting from the HTML Elements
function getWorkflowIDFromElements() {
    let id = $(`#bodied h3.text-center`).attr('name'); // get the id from the html tag
    return id;
}
// Get the id of current Work extracting from the HTML Elements
function getWorkIDFromElements() {
    let id = $("#bodied .worklist li .active").attr('name');
    return id;
}
// Get the id of current Command extracting from the HTML Elements
function getCmdIDFromElements() {
    let id = $(`#bodied .tab-pane.active .page-header`).attr('name'); // get the id from the html tag
    return id;
}
// Get the first object from ID value of workflows.json file
function getObjectFromID(data, id) {
    let rst = data.filter(obj => { return obj.id === `${id}` });
    if ( !rst || jQuery.isEmptyObject(rst) ) {
        return undefined;
    }
    rst = rst[0]; // get the firt(unique) element
    return rst;
}
// Get the list of index with the given attribute value
function getIndexParamsWithAttr(data, key, attr) {
    function findWithAttr(array, ke, at) {
        let rst = [];
        for(var i = 0; i < array.length; i += 1) {
            if(array[i][ke] === at) {
                rst.push(i);
            }
        }
        return rst;
    }
    let rst = findWithAttr(data, key, attr);
    if ( !rst || rst.length == 0 ) {
        return undefined;
    }
    return rst;
}
// Get the list of index with the given attribute value
function getIndexParamsWithKey(data, key) {
    function findWithAttr(array, ke) {
        let [rst,cnt] = [ [],[] ];
        for(var i = 0; i < array.length; i += 1) {
            if(ke in array[i]) {
                rst.push(i);
                cnt[i] = array[i][ke];
            }
        }
        return [rst,cnt];
    }
    let [rst,cnt] = findWithAttr(data, key);
    if ( !rst || rst.length == 0 || !cnt || cnt.length == 0 ) {
        return [undefined,undefined];
    }
    return [rst,cnt];
}
// Extract the main information from Workflow
function extractWorkflowAttributes() {
    // Get input parameters (from URL)
    let url_params = new URLSearchParams(window.location.search);
    let ptype = url_params.get('ptype');
    let pdir = url_params.get('pdir');
    let cdir = undefined;
    let wf_id = undefined;
    let cfg = undefined;
    let pdir_def = `${process.env.ISANXOT_LIB_HOME}`;
    

    // Check Project directory and Config directory of project
    if ( !ptype ) { // mandatory the value
        console.log(url_params);
        exceptor.showErrorMessageBox('Error Message', `Type of workflow is not defined`, end=true);
    }
    else if ( ptype == "load" ) { // load project
        cdir = `${pdir}/.isanxot`; // add the hidden folder where config files are saving
    }
    else if ( ptype == "samples" ) { // load local samples
        pdir = `${pdir_def}/${ptype}/${pdir}`; // add path
        cdir = `${pdir}/.isanxot`; // add the hidden folder where config files are saving
    }

    // Mandatory the project directory if 
    if ( !fs.existsSync(cdir) ) {
        console.log(url_params);
        exceptor.showErrorMessageBox('Error Message', `Config directory of project is not defined`, end=false, page=`${__dirname}/../index.html`);
    }

    // Add the most recent execution
    let d = getMostRecentDir(cdir);
    if ( !d ) {
        console.log(cdir);
        exceptor.showErrorMessageBox('Error Message', `Extracting the most recent execution`, end=true);
    }  
    cdir += `/${d}`;

    // Check if config file exits
    let cfgfile = `${cdir}/.cfg.yaml`;
    if ( !fs.existsSync(cfgfile) ) {
        console.log(cfgfile);
        exceptor.showErrorMessageBox('Error Message', `Openning the config file`, end=true, page=`${__dirname}/../index.html`);
    }
    else {
        // open config file
        cfg = jsyaml.safeLoad( fs.readFileSync(`${cfgfile}`, 'utf-8'));
        // get the wofkflow name
        if ( cfg.hasOwnProperty('name') ) wf_id = cfg['name'];
    }

    // Get workflow attributes from the wf_id
    let wfs = JSON.parse( fs.readFileSync(`${__dirname}/../wfs/workflows.json`) );
    let wf = getObjectFromID(wfs, wf_id);
    return [pdir_def, ptype, pdir, wf_id, wf, cdir, cfg];
}
// Check if two arrays are equal
function isEqual(a, b) {
    // if length is not equal 
    if(a.length!=b.length) {
        return false;
    } else { 
        // comapring each element of array 
        for(var i=0;i<a.length;i++) {
            if (a[i]!=b[i]) return false;
        }
        return true;
    }
}
// Check if all elements of array is empty
function allBlanks(arr) {
    for (var i = 0; i < arr.length; i++) {
        if (arr[i] != '' & arr[i] != null) return false;
    }
    return true;
}
  

// Export the In  the end of the day, calls to `require` returns exactly what `module.exports` is set to.
module.exports = {
    doneResizing:               doneResizing,
    importHTMLtemplate:         importHTMLtemplate,
    getWorkflowIDFromElements:  getWorkflowIDFromElements,
    getWorkIDFromElements:      getWorkIDFromElements,
    getCmdIDFromElements:       getCmdIDFromElements,
    getObjectFromID:            getObjectFromID,
    getIndexParamsWithAttr:     getIndexParamsWithAttr,
    getIndexParamsWithKey:      getIndexParamsWithKey,
    isEqual:                    isEqual,
    allBlanks:                  allBlanks
};


/*
 * Main
 */

// Import main templates
importHTMLtemplate(`${__dirname}/../sections/init.html`);
importHTMLtemplate(`${__dirname}/../sections/bodied.html`);
importHTMLtemplate(`${__dirname}/../sections/tabcontent.html`);
importHTMLtemplate(`${__dirname}/../sections/footer.html`);
importHTMLtemplate(`${__dirname}/../sections/executor.html`);
importHTMLtemplate(`${__dirname}/../sections/processor.html`);
importHTMLtemplate(`${__dirname}/../sections/logger.html`);
importHTMLtemplate(`${__dirname}/../sections/loader.html`);
importHTMLtemplate(`${__dirname}/../sections/helps/help_basic.html`);
importHTMLtemplate(`${__dirname}/../sections/helps/help_ptm.html`);
importHTMLtemplate(`${__dirname}/../sections/helps/help_lblfree.html`);

// Get input parameters (from URL)
let filename = path.basename(window.location.pathname,'.html');
if ( filename == "wf" ) {
    // Create and export the workflow attributes
    [
        pdir_def,
        ptype,
        pdir,
        wf_id,
        wf,
        cdir,
        wf_exec
    ] = extractWorkflowAttributes();
    wf_date_id = getWFDate();
    module.exports.pdir_def = pdir_def;
    module.exports.ptype = ptype;
    module.exports.pdir = pdir;
    module.exports.wf_date_id = wf_date_id;
    module.exports.wf_id = wf_id;
    module.exports.wf = wf;
    module.exports.cdir = cdir;
    module.exports.wf_exec = wf_exec;

    // add full-body 
    require(`./bodied`);
    // add the module to execute the jobs
    executor = require('./executor');
}
else if ( filename == "processes" ) {
    // add the module to process the jobs
    require('./processor');
}
else if ( filename == "index" ) {
    // for init page
    require(`./init`);
}
