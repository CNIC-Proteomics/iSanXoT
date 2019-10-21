// Remove console log in production mode
if (process.env.ISANXOT_MODE == "production") {
    console.log = function() {};
}

// set the local directory
process.env.ISANXOT_SRC_HOME = process.cwd();
