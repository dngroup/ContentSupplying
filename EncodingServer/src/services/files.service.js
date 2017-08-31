/**
 * Created by mlacaud on 14/08/17.
 */
var fs = require('fs');

var defaultPath = "./contents";


function createPathIfNotExist(path) {
    var pathTable = path.split('/');
    var currentPath = pathTable[0];
    for (var i = 0; i < pathTable.length; i++) {
        if (i > 0)
            currentPath += '/' +pathTable[i];
        if (!fs.existsSync(currentPath))
            fs.mkdirSync(currentPath);
    }
}

function createPathForFolder(folderName) {
    return defaultPath + "/" + folderName;
}

function getVideosInPath(path) {
    var listOfVideos = [];
    var files = fs.readdirSync(path);
    files.forEach(file => {
        if (file.indexOf("video.") > -1) {
            listOfVideos.push(file);
        }
    });
    return listOfVideos;
}

function getFoldersInPath(path) {
    var p = path;
    if (!path) {
        p = defaultPath;
    }
    var listOfFiles = fs.readdirSync(p).filter(f => fs.statSync(p+"/"+f).isDirectory());

    return listOfFiles
}

function readJson(path) {
    var data,
        obj = {};
    if (fs.existsSync(path)) {
        data = fs.readFileSync(path, 'utf8');
        obj = JSON.parse(data);
    }

    return obj;
}

function writeJson(path, obj) {
    var json = JSON.stringify(obj);
    fs.writeFileSync(path, json);
}

function getDefaultPath() {
    return defaultPath;
}

function removeFile(path) {
    fs.unlinkSync(path);
}

function removeFolder(path) {
    if( fs.existsSync(path) ) {
        fs.readdirSync(path).forEach(function(file,index){
            var curPath = path + "/" + file;
            if(fs.lstatSync(curPath).isDirectory()) { // recurse
                deleteFolderRecursive(curPath);
            } else { // delete file
                fs.unlinkSync(curPath);
            }
        });
        fs.rmdirSync(path);
    }
};

function exist(path) {
    return fs.existsSync(path);
}

function rename(oldPath, newPath) {
    fs.renameSync(oldPath, newPath);
}

function writeStream(path) {
    return fs.createWriteStream(path);
}

module.exports = {
    createPathIfNotExist: createPathIfNotExist,
    createPathForFolder: createPathForFolder,
    getVideosInPath: getVideosInPath,
    getFoldersInPath: getFoldersInPath,
    readJson: readJson,
    writeJson: writeJson,
    getDefaultPath: getDefaultPath,
    removeFile: removeFile,
    removeFolder: removeFolder,
    exist: exist,
    rename: rename,
    writeStream: writeStream
};