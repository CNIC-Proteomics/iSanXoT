/*
 * Import libraries
 */

let fs = require('fs');

/*
 * Local functions
 */

// Get the dirs in directory sorted by name
function getDirectories(source) {
    let files = [];
    try {
        files = fs.readdirSync(source, { withFileTypes: true })
            .filter(dirent => dirent.isDirectory())
            .map(dirent => dirent.name)
            .reverse();
    } catch (e) {
        console.log(`getting the folders in directory: ${e}`);
    }
    return files;
}
  
// Get the files in directory sorted by name
function getFiles(source) {
    let files = [];
    try {
        files = fs.readdirSync(source, { withFileTypes: true })
            .filter(dirent => dirent.isFile())
            .map(dirent => dirent.name);
    } catch (e) {
        console.log(`getting the files in directory: ${e}`);
    }
    return files;
}

// Get the most recent execution directory
// the files has to be sorted by name
function getMostRecentDir(dir) {  
    // the files/dirs has to be sorted by name
    let files = getDirectories(dir);
    return (files.length > 0)? files[0] : undefined;
}

// Sort the list of files by their extensions.
// The files with the same extension should be sorted by name.
function sortFilesByExt(files) {
    let arr = [];
    for (let x of files) { 
        let a =  x.split(/[\.]/g).filter(i => i.length > 0); 
        let b = '';
        if (a.length >= 2 && !x.endsWith('.')) b = a[a.length - 1];
        arr.push([b, x.replace(b, '')]);
    }
    return arr.sort().map(x => x[1].concat(x[0]));
}

// Read the header of file
function readHeaderFile(file) {
    let header = undefined;
    try {
        data = fs.readFileSync(file, 'utf8').toString().split('\n');
        for ( let i=0; i < data.length; i++) {
            if ( data[i] != '' ) {
                headers = data[i].split('\t');
                break;
            }
        }
        return headers;
    } catch (e) {
        console.log(`reading the headers: ${e}`);
    }
    return header;
}

// Get the column values from list of column indexes
// If the col list is undefined then return all values
function getColumnValuesFromFile(file, headers) {
    let vals = [];
    try {
        data = fs.readFileSync(file,'utf8').toString().split('\n');
        let isHeader = true;
        let cols = [];
        for ( let i=0; i < data.length; i++) {
            if ( data[i] != '' ) {
                // the first (not empty) line is the header
                // get the index of given headers
                if ( isHeader ) {
                    let dat = data[i].split('\t');
                    cols = headers.map(x => dat.indexOf(x));
                    isHeader = false;
                }
                // data lines
                // save the data into matrix (list of lists)
                else {
                    let dat = data[i].split('\t');
                    if ( cols === undefined ) {
                        vals.push(dat);
                    }
                    else if ( Array.isArray(cols) && cols.length > 0 ) {
                        let d = [];
                        for (let i=0; i<cols.length; i++) d.push(dat[cols[i]]);
                        vals.push(d);
                    }   
                }
            }
        }
        return vals;
    } catch (e) {
        console.log(`reading the vals: ${e}`);
    }
    return vals;
}

// Get an object of list from given ID
function getObjectFromID(data, id) {
    let rst = data.filter(obj => { return obj.id === `${id}` });
    if ( !rst || jQuery.isEmptyObject(rst) ) {
        return undefined;
    }
    rst = rst[0]; // get the firt(unique) element
    return rst;
}

// Get the list of index with the given attribute value
function getIndexParamsWithAttr(data, key, attr) {
    function findWithAttr(array, ke, at) {
        let rst = [];
        if (array === undefined) return rst;
        for(var i = 0; i < array.length; i += 1) {
            if(array[i][ke] === at) {
                rst.push(i);
            }
        }
        return rst;
    }
    let rst = findWithAttr(data, key, attr);
    if ( !rst || rst.length == 0 ) {
        return undefined;
    }
    return rst;
}

// Get the list of index with the given attribute value
function getIndexParamsWithKey(data, key) {
    function findWithAttr(array, ke) {
        let [rst,cnt] = [ [],[] ];
        if (array === undefined) return [rst,cnt];
        for(var i = 0; i < array.length; i += 1) {
            if(ke in array[i]) {
                rst.push(i);
                cnt[i] = array[i][ke];
            }
        }
        return [rst,cnt];
    }
    let [rst,cnt] = findWithAttr(data, key);
    if ( !rst || rst.length == 0 || !cnt || cnt.length == 0 ) {
        return [undefined,undefined];
    }
    return [rst,cnt];
}

// Check if two arrays are equal
function isEqual(a, b) {
    // if length is not equal 
    if(a.length!=b.length) {
        return false;
    } else { 
        // comapring each element of array 
        for(var i=0;i<a.length;i++) {
            if (a[i]!=b[i]) return false;
        }
        return true;
    }
}

// Check if all elements of array is empty
function allBlanks(arr) {
    for (var i = 0; i < arr.length; i++) {
        if (arr[i] != '' & arr[i] != null) return false;
    }
    return true;
}

// Check if any element of array is empty
function anyBlank(arr) {
    for (var i = 0; i < arr.length; i++) {
        if (arr[i] == '' || arr[i] == null) return true;
    }
    return false;
}

// Get all indexes of all ocurrences in array
function getAllIndexes(arr, val) {
    var indexes = [];
    for (var i = 0; i < arr.length; i++) {
        if (arr[i] === val) {
            indexes.push(i);
        }
    }
    return indexes;
}

// Remove the list of indexes from array
function removeListIndexes(arr, rem) {
    if ( rem && rem.length > 0 ) {
        for (var i = rem.length -1; i >= 0; i--) {
            arr.splice(rem[i], 1);
        }    
    }
    return arr;
}
  
/*
 * Functions for the Main Menu of app (main.js)
 */


// Export the In  the end of the day, calls to `require` returns exactly what `module.exports` is set to.
module.exports = {
    getDirectories:             getDirectories,
    getFiles:                   getFiles,
    getMostRecentDir:           getMostRecentDir,
    sortFilesByExt:             sortFilesByExt,
    readHeaderFile:             readHeaderFile,
    getColumnValuesFromFile:    getColumnValuesFromFile,
    getObjectFromID:            getObjectFromID,
    getIndexParamsWithAttr:     getIndexParamsWithAttr,
    getIndexParamsWithKey:      getIndexParamsWithKey,
    isEqual:                    isEqual,
    allBlanks:                  allBlanks,
    anyBlank:                   anyBlank,
    getAllIndexes:              getAllIndexes,
    removeListIndexes:          removeListIndexes
};
