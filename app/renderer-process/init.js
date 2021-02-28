/*
 * Import libraries
 */
let fs = require('fs');

// Extract the workflow attributes
let wfs = JSON.parse( fs.readFileSync(`${__dirname}/../wfs/workflows.json`));

// Create the html accordion for each workflow
// Go through the works of the workflow
let tpl = '';
for (var i = 0; i < wfs.length; i++) {
  let wf = wfs[i];
  let wf_id = wf['id'];
  let wf_label = wf['label'];
  let wf_sdesc = wf['sdesc'];
  let wf_samples = wf['samples'];
  let tpl_samples = '';
  for (var j = 0; j < wf_samples.length; j++) {
    let wf_s = wf_samples[j];
    // tpl_samples += `<a href="wf.html?ptype=samples&pdir=${wf_s['id']}" class="stretched-link text-info">${wf_s['name']}</a> | `;
    tpl_samples += `<a class="dropdown-item" href="wf.html?ptype=samples&pdir=${wf_s['id']}" class="stretched-link text-info">${wf_s['name']}</a>`;
  }
  // tpl_samples = tpl_samples.replace(/\s+\|\s+$/g, '');
  tpl += `
  <div id="init_wf_${wf_id}" class="card">
  <div class="card-header" id="heading${i}" data-toggle="collapse" data-target="#collapse${i}" aria-expanded="false" aria-controls="collapse${i}">${wf_label}</div>    
  <div id="collapse${i}" class="collapse" aria-labelledby="heading${i}" data-parent="#accordion">
    <div class="card-body">
        <p>${wf_sdesc}</p>
        <div class="row">
          <div class="btn-group col-md-2 ml-md-auto">
            <div class="btn-group dropleft" role="group">
              <button type="button" class="btn btn-secondary dropdown-toggle dropdown-toggle-split" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
                <span class="sr-only">Toggle Dropleft</span>
              </button>
              <div class="dropdown-menu">${tpl_samples}</div>
            </div>
            <a href="wf.html?ptype=load&pdir=${__dirname}/../wfs/${wf_id}" class="btn btn-primary active" role="button" aria-pressed="true">Go to workflow</a>
          </div>
        </div>
    </div>
  </div>
  </div>
  `;
}
// Add the accordion
$(`#init #accordion`).html(`${tpl}`);
// Expand the first element
$(`#init #accordion #heading0`).attr('aria-expanded',true);
$(`#init #accordion #collapse0`).attr('class','show');

