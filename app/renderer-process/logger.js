class log { 
  constructor(pid, file, name) {
    this.pid  = pid;
    this.file = file;
    this.name = name;
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