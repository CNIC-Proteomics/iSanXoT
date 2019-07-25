// Remove console log in production mode
if (process.env.ISANXOT_MODE == "production") {
    console.log = function() {};
}

// Get workflow id
let wfid = window.location.href.split("wfid=")[1];
// Import workflow template
let fs = require('fs');
let path = require('path');
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
importHTMLtemplate(`${__dirname}/../sections/footer.html`);
importHTMLtemplate(`${__dirname}/../sections/executor.html`);
importHTMLtemplate(`${__dirname}/../sections/processor.html`);
importHTMLtemplate(`${__dirname}/../sections/processes.html`);
importHTMLtemplate(`${__dirname}/../sections/advance/help_adv.html`);
importHTMLtemplate(`${__dirname}/../sections/lblfree/help_lblfree.html`);

// Import workflow templates
// add workflow modules: specific modules, processor, exceptor
if ( wfid !== undefined ) {
    if ( wfid.includes("advance") ) {
        importHTMLtemplate(`${__dirname}/../sections/advance/main.html`);
        importHTMLtemplate(`${__dirname}/../sections/advance/tasks.html`);
        importHTMLtemplate(`${__dirname}/../sections/advance/tasktable.html`);
        importHTMLtemplate(`${__dirname}/../sections/advance/params-pratio.html`);
        var tasktable = require(`./advance/tasktable`);
        var parameters = require('./advance/parameters');
        require('./advance/samples');
    }
    else if ( wfid.includes("lblfree") ) {
        importHTMLtemplate(`${__dirname}/../sections/lblfree/main.html`);
        importHTMLtemplate(`${__dirname}/../sections/lblfree/tasks.html`);
        importHTMLtemplate(`${__dirname}/../sections/lblfree/tasktable.html`);
        var tasktable = require('./lblfree/tasktable');
        var parameters = require('./lblfree/parameters');
        require('./lblfree/samples');
    }
    // add the module to process the jobs
    require('./processor');

    // Export the In  the end of the day, calls to `require` returns exactly what `module.exports` is set to.
    module.exports.tasktable = tasktable;
    module.exports.parameters = parameters;
}

