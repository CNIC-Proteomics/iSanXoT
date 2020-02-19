/*
 * Import libraries
 */
let fs = require('fs');

// Extract the workflow attributes
let wfs = JSON.parse( fs.readFileSync(`${__dirname}/../data/workflows.json`));

// Create the html accordion for each workflow
// Go through the works of the workflow
let tpl = '';
for (var i = 0; i < wfs.length; i++) {
  let wf = wfs[i];
  let wf_id = wf['id'];
  let wf_label = wf['label'];
  let wf_sdesc = wf['sdesc'];
  tpl += `
  <div id="init_wf_${wf_id}" class="card">
  <div class="card-header" id="heading${i}" data-toggle="collapse" data-target="#collapse${i}" aria-expanded="false" aria-controls="collapse${i}">${wf_label}</div>    
  <div id="collapse${i}" class="collapse" aria-labelledby="heading${i}" data-parent="#accordion">
    <div class="card-body">
        <p>${wf_sdesc}</p>
        <div class="text-right">
          <a href="wf.html?wfid=${wf_id}&pdir=${__dirname}/../data" class="btn btn-primary active" role="button" aria-pressed="true">Go to workflow</a>
        </div>
    </div>
  </div>
  </div>
  `;
}
// Add the accordion
$(`#init #accordion`).html(`${tpl}`);