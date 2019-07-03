const links = document.querySelectorAll('link[rel="import"]')

// Import and add each page to the DOM
Array.prototype.forEach.call(links, function (link) {
    let template = link.import.querySelector('.task-template');
    let clone = document.importNode(template.content, true);
    let tid = template.id;
    document.querySelector('#'+tid).appendChild(clone);
})
