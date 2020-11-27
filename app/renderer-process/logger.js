class log { 
  constructor(pid, file, name) {
    this.pid  = pid;
    this.file = file;
    this.name = name;
  }
  readLogFile() {
    fs.readFile(this.file, 'utf8', function(err, contents) {
      console.log(this.file);
      console.log(contents);
    });
    console.log('after calling readFile');  
  }
}

// class logger extends log {
//   constructor(name) {
//     super(name); // call the super class constructor and pass in the name parameter
//   }

//   speak() {
//     console.log(`${this.name} barks.`);
//   }
// }

// now we export the class, so other modules can create Cat objects
module.exports = {
  log: log
}