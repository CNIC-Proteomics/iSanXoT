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


/*
 * Local functions
 */

// Import workflow template
function importHTMLtemplate(wfhref, tid) {
    if (!tid) tid = `#${path.basename(wfhref, '.html')}`;
    if ( document.querySelector(`${tid}`) !== null ) {
        let s = fs.readFileSync(wfhref);
        let frag = document.createRange().createContextualFragment(s.toString());
        let template = frag.querySelector('.task-template');
        let clone = document.importNode(template.content, true);
        document.querySelector(`${tid}`).appendChild(clone);
    }
};

// Resize table from the window size
var resizeId = null;
function doneResizing() {
    // resize table from the window size
    let winwidth = $(window).width();
    let winheight = $(window).height();    
    if ( $('.tab-content').length ) {
        let newheight = winheight - 165;
        $(`.tab-content`).height(newheight);
    }
    if ( $('#hot_processes_panel').length ) {
        let newheight = winheight - 175;
        $(`#hot_processes_panel`).height(newheight);
    }
}

// Function when the windows is resize
$(window).resize(function() {
    clearTimeout(resizeId);
    resizeId = setTimeout(doneResizing, 250);
});
// Operations when the html document is ready
$(document).ready(function() {
    doneResizing();
});

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
// Get the list of optionals parameters from workflows.json file
function getIndexParamsFromType(data, t) {
    function findWithAttr(array, attr, value) {
        let rst = [];
        for(var i = 0; i < array.length; i += 1) {
            if(array[i][attr] === value) {
                rst.push(i);
            }
        }
        return rst;
    }
    let rst = findWithAttr(data, 'type', t);
    if ( !rst || rst.length == 0 ) {
        return undefined;
    }
    return rst;
}
// Extract the main information from Workflow
function extractWorkflowAttributes() {
    // Get input parameters (from URL)
    let url_params = new URLSearchParams(window.location.search);
    let pdir = url_params.get('pdir');
    let wf_id = url_params.get('wfid');
    let cfg = undefined;
    let pdir_def = `${__dirname}/../data`;

    // Apply depending the type of workflow
    if ( !wf_id ) { // mandatory the value
        console.log(url_params);
        exceptor.showErrorMessageBox('Error Message', `Type of workflow is not defined`, end=true);
    }
    else if ( wf_id == "load" ) { // load the workflow

        // pdir = 'S:\\LAB_JVC\\RESULTADOS\\JM RC\\iSanXoT\\tests\\PESA omicas\\3a_Cohorte_120_V2_results'
        // pdir = 'S:\\LAB_JVC\\RESULTADOS\\JM RC\\iSanXoT\\test_2'

        // Add the hidden folder where config files are saving
        pdir += '/.isanxot'

        // Mandatory the project directory if 
        if ( !fs.existsSync(pdir) ) {
            console.log(url_params);
            exceptor.showErrorMessageBox('Error Message', `Project directory is not defined`, end=false, page=`${__dirname}/../index.html`);
        }

        // Add the most recent execution
        let d = getMostRecentDir(pdir);
        if ( !d ) {
            console.log(pdir);
            exceptor.showErrorMessageBox('Error Message', `Extracting the most recent execution`, end=true);
        }  
        pdir += `/${d}`;

        // Check if config file exits
        let cfgfile = `${pdir}/config.yaml`;
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
    }
    else { // default workflow. Add the local directory with the data files of workflow        
        pdir = `${pdir_def}/${wf_id}`;
    }

    // Get workflow attributes from the wf_id
    let wfs = JSON.parse( fs.readFileSync(`${__dirname}/../data/workflows.json`) );
    let wf = getObjectFromID(wfs, wf_id);
    return [pdir_def, pdir, wf_id, wf, cfg];
}


// Export the In  the end of the day, calls to `require` returns exactly what `module.exports` is set to.
module.exports.importHTMLtemplate = importHTMLtemplate;
module.exports.getWFDate = getWFDate;
module.exports.getWorkflowIDFromElements = getWorkflowIDFromElements;
module.exports.getWorkIDFromElements = getWorkIDFromElements;
module.exports.getCmdIDFromElements = getCmdIDFromElements;
module.exports.getObjectFromID = getObjectFromID;
module.exports.getIndexParamsFromType = getIndexParamsFromType;

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
importHTMLtemplate(`${__dirname}/../sections/helps/basic.html`);
importHTMLtemplate(`${__dirname}/../sections/helps/ptm.html`);
importHTMLtemplate(`${__dirname}/../sections/helps/lblfree.html`);

// Get input parameters (from URL)
let filename = path.basename(window.location.pathname,'.html');
if ( filename == "wf" ) {
    // Export workflow attributes
    [
        module.exports.pdir_def,
        module.exports.pdir,
        module.exports.wf_id,
        module.exports.wf,
        module.exports.wf_exec
    ] = extractWorkflowAttributes();    
    // add full-body 
    require(`./bodied`);
    // add the module to execute the jobs
    require('./executor');
}
else if ( filename == "processes" ) {
    // add the module to process the jobs
    require('./processor');
}
else if ( filename == "index" ) {
    // for init page
    require(`./init`);
}
