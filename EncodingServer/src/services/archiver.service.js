/**
 * Created by mlacaud on 21/08/17.
 */

var archiver = require('archiver');
var filesservice = require('./files.service');

function archiveVideoFiles(folderPath) {
    return archive(folderPath.encodedPath, folderPath.archivePath, folderPath.videoId);
}

function archive(inputPath, outputPath, directoryInZip) {
    var testInterval = 2000;
    return new Promise(function(done, reject) {
        var archiving = function() {
            var output = filesservice.writeStream(outputPath + '.tmp');

            var archive = archiver('zip');

            // listen for all archive data to be written
            output.on('close', function () {
                filesservice.rename(outputPath + '.tmp', outputPath);
                done();
            });

            // good practice to catch warnings (ie stat failures and other non-blocking errors)
            archive.on('warning', function (err) {
                if (err.code === 'ENOENT') {
                    reject(err);
                } else {
                    // throw error
                    //throw err;
                    reject(err);
                }
            });

            // good practice to catch this error explicitly
            archive.on('error', function (err) {
                //throw err;
                reject(err);
            });

            archive.pipe(output);

            archive.directory(inputPath, directoryInZip);

            archive.finalize();
        };
        if (!filesservice.exist(outputPath + '.tmp')) {
            archiving();
        } else {
            var testExist = function() {
                if (!filesservice.exist(outputPath + '.tmp') && filesservice.exist(outputPath)) {
                  done();
                }
                if (!filesservice.exist(outputPath + '.tmp') && !filesservice.exist(outputPath)) {
                    archiving();
                }
            };
            setTimeout(testExist, testInterval);
        }
    });
}

module.exports = {
    archiveVideoFiles: archiveVideoFiles
};
