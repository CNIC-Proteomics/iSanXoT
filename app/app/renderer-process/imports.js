/*
 * Import libraries
 */

let fs = require('fs');
let path = require('path');

const { ipcRenderer } = require('electron');
const { dialog } = require('electron').remote;

/*
 * Window size
 */

// Resize table from the window size
var resizeId = null;
function doneResizing() {
    let winheight = $(window).height();
    let outerheight = $('.tab-content').outerHeight(); // content height
    if ( $('.tab-content').length ) {
        let newheight = winheight - 142;
        $(`.tab-content`).height(newheight);
        // get the maximum height for sideber
        if ( outerheight > $(`#sidebar`).height() ) $(`#sidebar`).height(outerheight);
    }

}

// Function when the windows is resize
$(window).resize(function() {
    clearTimeout(resizeId);
    resizeId = setTimeout(doneResizing, 250);
});
// Operations when the windows is loaded
$(window).on('load', function() {
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
    // stop any loading panel
    exceptor.stopLoadingWorkflow();
});

/*
 * Renderer functions
 */
ipcRenderer.on('newProject',  function() {
    projector.newProject();
});
ipcRenderer.on('openProject',  function() {
    let prj_dir = dialog.showOpenDialogSync({ properties: ["openDirectory"] });
    if ( prj_dir !== undefined ) {
        exceptor.loadingWorkflow(); // loading...
        projector.openProject(prj_dir);
        // stopLoadingWorkflow function done when the page is loaded
    }
});
ipcRenderer.on('saveProject', function() {
    // loading...
    exceptor.loadingWorkflow();
    setTimeout(function() {
        let [prj_id,prj_dir,dte_dir] = projector.saveProject();
        // everything was alright
        exceptor.stopLoadingWorkflow();
        exceptor.showMessageBox('info', "Your project has been saved successfully", title='Save project');
    }, 1000); // due the execSync block everything, we have to wait until loading event is finished
});
ipcRenderer.on('importWorkflow', function() {
    let wkf_dir = dialog.showOpenDialogSync({ properties: ["openDirectory"], defaultPath: process.env.ISANXOT_SAMPLES_DIR });
    if ( wkf_dir !== undefined ) {
        exceptor.loadingWorkflow(); // loading...
        workflower.importWorkflow(wkf_dir);
        // stopLoadingWorkflow function done when the page is loaded
    }
});
ipcRenderer.on('exportWorkflow', function() {
    let wkf_dir = dialog.showOpenDialogSync({ properties: ["openDirectory"] });
    if ( wkf_dir !== undefined ) {
        // loading...
        exceptor.loadingWorkflow();
        setTimeout(function() {  
            workflower.exportWorkflow(wkf_dir);
            // everything was alright
            exceptor.stopLoadingWorkflow();
            exceptor.showMessageBox('info', "Your workflow has been exported successfully", title='Export workflow');
        }, 1000); // due the execSync block everything, we have to wait until loading event is finished
    }
});
ipcRenderer.on('importAdaptor', (event, data) => {
    // loading...
    exceptor.loadingWorkflow();
    let adaptor_dir = data.dir;
    workflower.importAdaptor(adaptor_dir);
    // stopLoadingWorkflow function done when the page is loaded
});
ipcRenderer.on('openHelper',  (event, data) => {
    helper.openHelper(data);
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

// Enable/Disable the menu items related to workflow
function setEnableMenuItem(val) {
    if ( process.env.ISANXOT_ADAPTOR_HOME !== undefined ) {
        const { Menu } = require('electron').remote;
        let mainMenu = Menu.getApplicationMenu();
        mainMenu.getMenuItemById('save-project').enabled = val;
        mainMenu.getMenuItemById('import-workflow').enabled = val;
        mainMenu.getMenuItemById('export-workflow').enabled = val;
        // enable/disable adaptors
        mainMenu.getMenuItemById('adaptors').enabled = val;
        let dirs = fs.readdirSync(process.env.ISANXOT_ADAPTOR_HOME, { withFileTypes: true }).filter(dirent => dirent.isDirectory()).map(dirent => dirent.name);
        for (let i=0; i<dirs.length; i++) {
            let adaptor_dir = dirs[i];
            let adaptor_wf = JSON.parse(fs.readFileSync(path.join(process.env.ISANXOT_ADAPTOR_HOME, `${adaptor_dir}/adaptor.json`)));
            let adaptor_id = adaptor_wf['id'];
            if ( mainMenu.getMenuItemById(adaptor_id) ) mainMenu.getMenuItemById(adaptor_id).enabled = val;
        }
        // enable/disable proccesses
        mainMenu.getMenuItemById('processes').enabled = val;
        mainMenu.getMenuItemById('processes-main').enabled = val;    
    }
};

// Extract the main information from Workflow
function extractWorkflowAdaptorAttributes() {
    // Get input parameters (from URL)
    let url_params = new URLSearchParams(window.location.search);
    let prj_dir = url_params.get('pdir');
    let wkf_dir = url_params.get('wdir');
    let adp_dir = url_params.get('adir');
    if ( wkf_dir === undefined || adp_dir === undefined ) {
        // disable the menu items related with workflow
        setEnableMenuItem(false);
        // Exceptions
        if ( wkf_dir === undefined ) {
            exceptor.showErrorMessageBox('Error Message', `Workflow directory within project is not defined`, end=false, page=`${__dirname}/../index.html`);
        }
        if ( adp_dir === undefined ) {
            exceptor.showErrorMessageBox('Error Message', `Adaptor directory within project is not defined`, end=false, page=`${__dirname}/../index.html`);
        }
    }

    // Get the project structure (config file, if exits)
    let prj_cfg = projector.getProjectCfg(prj_dir);

    // Get the workflow structure
    let wkf = workflower.extractWorkflowStr();

    // Get the adaptor structure
    let adp = workflower.extractAdaptorStr(adp_dir);

    // Join the adaptor strcuture and workflow structure
    let wf = workflower.joinWorkflowAdaptorStr(adp, wkf);

    return [prj_dir, wkf_dir, adp_dir, prj_cfg, wf];
}

// Export the In  the end of the day, calls to `require` returns exactly what `module.exports` is set to.
module.exports = {
    doneResizing:               doneResizing,
    importHTMLtemplate:         importHTMLtemplate
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
importHTMLtemplate(`${__dirname}/../iSanXoT-Help.html`);

// Import scripts
let exceptor = require('./exceptor');
let helper = require('./helper');
let projector = require('./projector');
let workflower = require('./workflower');

// Get input parameters (from URL)
let filename = path.basename(window.location.pathname,'.html');
if ( filename == "wf" ) {
    // Get the workflow attributes
    let [prj_dir, wkf_dir, adp_dir, prj_cfg, wf] = extractWorkflowAdaptorAttributes();
    // Export the attributes
    module.exports.prj_dir = prj_dir;
    module.exports.wkf_dir = wkf_dir;
    module.exports.adp_dir = adp_dir;
    module.exports.prj_cfg = prj_cfg;
    module.exports.wf = wf;

    // add full-body
    require(`./bodied`);

    // enable menu items related with workflow
    setEnableMenuItem(true);
}
else if ( filename == "processes" ) {
    // add the module to process the jobs
    require('./processor');

    // Disable the menu items related with workflow
    setEnableMenuItem(false);
}
else if ( filename == "index" ) {
    // for init page (deprecated)
    // require(`./init`);

    // Disable the menu items related with workflow
    setEnableMenuItem(false);
}
