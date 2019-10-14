// Remove console log in production mode
if (process.env.ISANXOT_MODE == "production") {
    console.log = function() {};
}

// Import libraries
let fs = require('fs');
let path = require('path');

// Get workflow id
let wfid = window.location.href.split("wfid=")[1];
var url = window.location.pathname;
var filename = path.basename(url,'.html');

// Import workflow template
function importHTMLtemplate(wfhref) {
    var tid = path.basename(wfhref, '.html');
    if ( document.querySelector(`#${tid}`) !== null ) {
        let s = fs.readFileSync(wfhref);
        let frag = document.createRange().createContextualFragment(s.toString());
        let template = frag.querySelector('.task-template');
        let clone = document.importNode(template.content, true);
        document.querySelector(`#${tid}`).appendChild(clone);
    }
};

// Import main templates
importHTMLtemplate(`${__dirname}/../sections/init.html`);
importHTMLtemplate(`${__dirname}/../sections/footer.html`);
importHTMLtemplate(`${__dirname}/../sections/executor.html`);
importHTMLtemplate(`${__dirname}/../sections/executor.html`);
importHTMLtemplate(`${__dirname}/../sections/processor.html`);
importHTMLtemplate(`${__dirname}/../sections/logger.html`);
importHTMLtemplate(`${__dirname}/../sections/loader.html`);
importHTMLtemplate(`${__dirname}/../sections/basic/help_basic.html`);
importHTMLtemplate(`${__dirname}/../sections/ptm/help_ptm.html`);
importHTMLtemplate(`${__dirname}/../sections/lblfree/help_lblfree.html`);

// Import workflow templates
// add workflow modules: specific modules, processor, exceptor
if ( wfid !== undefined ) {
    if ( wfid.includes("basic") ) {
        importHTMLtemplate(`${__dirname}/../sections/basic/main.html`);
        importHTMLtemplate(`${__dirname}/../sections/basic/tasks.html`);
        importHTMLtemplate(`${__dirname}/../sections/basic/tasktable.html`);
        importHTMLtemplate(`${__dirname}/../sections/basic/params-pratio.html`);
        var tasktable = require(`./basic/tasktable`);
        var parameters = require('./basic/parameters');
        require('./basic/samples');
    }
    else if ( wfid.includes("ptm") ) {
        importHTMLtemplate(`${__dirname}/../sections/ptm/main.html`);
        importHTMLtemplate(`${__dirname}/../sections/ptm/tasks.html`);
        importHTMLtemplate(`${__dirname}/../sections/ptm/tasktable.html`);
        var tasktable = require('./ptm/tasktable');
        var parameters = require('./ptm/parameters');
        require('./ptm/samples');
    }
    else if ( wfid.includes("lblfree") ) {
        importHTMLtemplate(`${__dirname}/../sections/lblfree/main.html`);
        importHTMLtemplate(`${__dirname}/../sections/lblfree/tasks.html`);
        importHTMLtemplate(`${__dirname}/../sections/lblfree/tasktable.html`);
        var tasktable = require('./lblfree/tasktable');
        var parameters = require('./lblfree/parameters');
        require('./lblfree/samples');
    }
    // add the module to execute the jobs
    // require('./processor');
    require('./executor');

    // Export the In  the end of the day, calls to `require` returns exactly what `module.exports` is set to.
    module.exports.tasktable = tasktable;
    module.exports.parameters = parameters;
}
else {
    if ( filename == "processes" ) {
        // add the module to process the jobs
        require('./processor');
    }
}


