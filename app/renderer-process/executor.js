const { ipcRenderer } = require('electron');

/*
  Global variables
*/
let cProcess = require('child_process');
let psTree = require(process.env.ISANXOT_NODE_PATH + '/ps-tree')
let proc = null;


function appendToDroidOutput(msg) {
  let elem = document.getElementById("droid-output"); 
  elem.value += msg;
}

function backgroundProcess(cmd) {
  // eexecute command line
  proc = cProcess.exec( cmd );

  // send the process id to main js
  ipcRenderer.send('pid-message', proc.pid);

  // psTree(proc.pid, function (err, children) {  // check if it works always
  //   children.map(function (p) {
  //     console.log( 'Process %s has been killed!', p.PID );
  //     // ipcRenderer.send('pid-message', p.PID );
  //     // process.kill(p.PID);           
  //   });
  // });


  // psTree(proc.pid, function (err, children) {  // check if it works always
  //   children.map(function (p) {
  //     console.log( 'Process %s has been killed!', p.PID );
  //     ipcRenderer.send('pid-message', p.PID );
  //     process.kill(p.PID);                
  //   });
  // });


  proc.stdout.on('data', (data) => {
    appendToDroidOutput(data);
    console.log(`stdout: ${data}`);
  });

  proc.stderr.on('data', (data) => {
    appendToDroidOutput(data);
    console.log(`stderr: ${data}`);
  });

  // Handle on exit event
  proc.on('close', (code) => {
    var preText = `Child exited with code ${code} : `;
    switch(code){
        case 0:
            console.info(preText+"Something unknown happened executing the batch.");
            break;
        case 1:
            console.info(preText+"The file already exists");
            break;
        case 2:
            console.info(preText+"The file doesn't exists and now is created");
            break;
        case 3:
            console.info(preText+"An error ocurred while creating the file");
            break;
    }
    document.querySelector('#executor #start').disabled = false;
    document.querySelector('#executor #stop').disabled = true;
  });

};

/*
 * Click Executor
 */
document.querySelector('#executor #start').addEventListener('click', function() {

  // get the type of Workflow
  let smkfile = tasktable.smkfile;
  let cfgfile = tasktable.cfgfile;

  // Check and retrieves parameters depending on the type of workflow
  let params = parameters.createParameters(cfgfile);
  if ( params ) {
    // Execute the workflow
    let cmd_smk = `"${process.env.ISANXOT_PYTHON3x_HOME}/tools/Scripts/snakemake.exe" --configfile "${params.cfgfile}" --snakefile "${smkfile}" --cores ${params.nthreads} --directory "${params.outdir}" `;
    let cmd = `${cmd_smk} --unlock && ${cmd_smk} --rerun-incomplete `;
    console.log( cmd );
    backgroundProcess( cmd );
    // active the log tab
    $('.nav-tabs a#processes-tab').tab('show');
    // disable Start button
    document.querySelector('#executor #start').disabled = true;
    document.querySelector('#executor #stop').disabled = false;
  }

});

// Kill all shell processes
document.querySelector('#executor #stop').addEventListener('click', function() {
  if ( proc !== null ) {
    let sms = "Look for child processes from: "+proc.pid+"\n";
    console.log(sms);
    appendToDroidOutput("\n\nThe processes have been stopped!\n\n");
    psTree(proc.pid, function (err, children) {  // check if it works always
      children.forEach(function (p) {
        let sms = "Process has been killed!"+p.PID+"\n";
        console.log(sms);
        process.kill(p.PID); 
      });
      // enable the Start button
      document.querySelector('#executor #start').disabled = false;
      document.querySelector('#executor #stop').disabled = true;
      });
  }
});
