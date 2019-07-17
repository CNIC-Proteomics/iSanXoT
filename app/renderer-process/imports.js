// Remove console log in production mode
if (process.env.ISANXOT_MODE == "production") {
    console.log = function() {};
}

// // Import and add each page to the DOM
// const links = document.querySelectorAll('link[rel="import"]');
// Array.prototype.forEach.call(links, function (link) {
//     let template = link.import.querySelector('.task-template');
//     let clone = document.importNode(template.content, true);
//     let tid = template.id;
//     if ( document.querySelector('#'+tid) !== null ) {
//         document.querySelector('#'+tid).appendChild(clone);
//     }
// });

// Get workflow id
var wfid = window.location.href.split("wfid=")[1];
// Import workflow template
let fs = require('fs');
let path = require('path');
function importHTMLtemplate(wfhref) {
    var tid = path.basename(wfhref, '.html');
    if ( document.querySelector(`#${tid}`) !== null ) {
        
        console.log(tid);

        let s = fs.readFileSync(wfhref);
        let frag = document.createRange().createContextualFragment(s.toString());
        let template = frag.querySelector('.task-template');
        let clone = document.importNode(template.content, true);
        document.querySelector(`#${tid}`).appendChild(clone);
    }
};

// Import workflow templates
// Add workflow modules
if ( wfid !== undefined ) {
    if ( wfid == "advance" ) {
        importHTMLtemplate(`${__dirname}/../sections/advance/main.html`);
        importHTMLtemplate(`${__dirname}/../sections/advance/tasktable.html`);
        importHTMLtemplate(`${__dirname}/../sections/advance/params_pratio.html`);
        var tasktable = require(`./advance/tasktable`);
        require('./advance/samples');
    }
    else if ( wfid == "lblfree" ) {
        importHTMLtemplate(`${__dirname}/../sections/lblfree/main.html`);
        importHTMLtemplate(`${__dirname}/../sections/lblfree/tasktable.html`);
        var tasktable = require('./lblfree/tasktable');
        require('./lblfree/samples');
    }
}

// Import main templates
importHTMLtemplate(`${__dirname}/../sections/footer.html`);
importHTMLtemplate(`${__dirname}/../sections/executor.html`);
importHTMLtemplate(`${__dirname}/../sections/processes.html`);
importHTMLtemplate(`${__dirname}/../sections/advance/help_adv.html`);
importHTMLtemplate(`${__dirname}/../sections/lblfree/help_lblfree.html`);


// We assign properties to the `module.exports` property, or reassign `module.exports` it to something totally different.
// In  the end of the day, calls to `require` returns exactly what `module.exports` is set to.
module.exports.tasktable = tasktable;
