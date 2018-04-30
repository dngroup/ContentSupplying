/**
 * Created by mlacaud on 21/08/17.
 */
var filesservice = require("../services/files.service");

/**
 * FolderPath
 *
 * {string} videoId
 * {string} folderPath
 * {string} tmpPath
 * {string} statePath
 * {string} encodedPath
 * {string} thumbnailPath
 * {string} videoPath
 * {string} archivePath
 * {string} queuePath
 *
 */
class FolderPath {
    constructor(obj) {
        this.videoId = obj.videoId || 'default';

        var defaultFolderPath = "./contents/" + this.videoId;

        this.folderPath =  obj.folderPath || defaultFolderPath;
        this.tmpPath = obj.tmpPath || this.folderPath + '/tmp';
        this.statePath = obj.statePath || this.folderPath + '/state.json';
        this.encodedPath =  obj.encodedPath || this.folderPath + '/' + this.videoId;
        this.thumbnailPath = obj.thumbnailPath || this.encodedPath + '/thumbnail.png';
        this.videoPath = obj.videoPath || this.folderPath + '/' + filesservice.getVideosInPath(this.folderPath)[0];
        this.archivePath = obj.archivePath || this.folderPath + '/' + this.videoId + ".zip";
        this.queuePath = obj.queuePath || filesservice.getDefaultPath() + '/queue.json';
    }
}

exports.FolderPath = FolderPath;