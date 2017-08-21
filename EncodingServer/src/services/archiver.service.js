/**
 * Created by mlacaud on 21/08/17.
 */
var fs = require('fs');
var archiver = require('archiver');
var filesservice = require('./files.service');

function archiveVideoFiles(folderPath) {
    archive(folderPath.archivePath);
}

function archive(path) {
    var output = fs.createWriteStream(__dirname + '/example.zip');
    var archive = archiver('zip');

    // listen for all archive data to be written
    output.on('close', function() {
        console.log(archive.pointer() + ' total bytes');
        console.log('archiver has been finalized and the output file descriptor has closed.');
    });

    // good practice to catch warnings (ie stat failures and other non-blocking errors)
    archive.on('warning', function(err) {
        if (err.code === 'ENOENT') {
            // log warning
        } else {
            // throw error
            throw err;
        }
    });

    // good practice to catch this error explicitly
    archive.on('error', function(err) {
        throw err;
    });

}

modules.export = {
    archiveVideoFiles: archiveVideoFiles
};
