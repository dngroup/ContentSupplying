/**
 * Created by mlacaud on 21/08/17.
 */
var filesservice = require("../services/files.service");

/**
 * FolderPath
 *
 * {string} folderPath
 * {string} tmpPath
 * {string} statePath
 * {string} encodedPath
 * {string} videoPath
 * {string} archivePath
 *
 */
class FolderPath {
    constructor(obj, videoId) {
        var defaultFolderPath = "./contents/" + videoId;

        this.folderPath =  obj.folderPath || defaultFolderPath;
        this.tmpPath = obj.tmpPath || this.folderPath + '/tmp';
        this.statePath = obj.statePath || this.folderPath + '/state.json';
        this.encodedPath =  obj.encodedPath || this.folderPath + '/' + videoId;
        this.videoPath = obj.videoPath || this.folderPath + '/' + filesservice.getVideosInPath(this.folderPath)[0];
        this.archivePath = obj.archivePath || this.folderPath + '/' + videoId + ".zip";
    }
}

exports.FolderPath = FolderPath;