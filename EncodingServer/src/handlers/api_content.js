/**
 * Created by mlacaud on 14/08/17.
 */
var {EncodingParameter} = require('../models/encodingparameter');
var {VideoInfo} = require('../models/videoinfo');
var fs = require('fs');
var fileservice = require('../services/files.service');
var encodingservice = require('../services/encoding.service');
var queueservice = require('../services/queue.service');
var path = require('path');
var mmm = require('mmmagic');
var {Magic} = require('mmmagic');
var mime = require('mime-types');
var path = require('path');

function getAllVideosWithInfos(req, res) {
    var result = [];
    var videos = fileservice.getFoldersInPath();
    var obj;
    var infos;
    var infosFile = [];
    for (var i in videos) {
        obj = fileservice.readJson(path.join(fileservice.createPathForFolder(videos[i]), 'state.json'));
        if (Object.keys(obj).length !== 0 || obj.constructor !== Object) {
            infosFile.push(path.join(fileservice.createPathForFolder(videos[i]), videos[i], 'infos.json'));
            infosFile.push(path.join(fileservice.createPathForFolder(videos[i]), 'infos.json'));
            for (var j in infosFile) {
                if (fileservice.exist(infosFile[j])) {
                    infos = fileservice.readJson(infosFile[j]);
                    break;
                }
            }
            infosFile = [];
            result.push({videoId: obj.videoId, infos: infos});
        }
    }

    res.send(result);
}

module.exports = {
    addApi: function (app) {

        /**
         *   Get a list of the videos on the file system
         *
         */
        app.get('/api/encode', getAllVideosWithInfos);

        /**
         *   Get a list of the videos on the file system
         *
         */
        app.get('/api/encode/infos', getAllVideosWithInfos);

        /**
         *   Get the infos of a video on the file system
         *
         */
        app.get('/api/encode/infos/:videoid', function (req, res) {
            var result = [];
            var videos = fileservice.getFoldersInPath();
            var obj;
            var infos;
            var infosFile = [];
            var videoId = req.params.videoid;
            if (fileservice.exist(fileservice.createPathForFolder(videoId))) {
                obj = fileservice.readJson(path.join(fileservice.createPathForFolder(videoId), 'state.json'));
                if (Object.keys(obj).length !== 0 || obj.constructor !== Object) {
                    infosFile.push(path.join(fileservice.createPathForFolder(videoId), videoId, 'infos.json'));
                    infosFile.push(path.join(fileservice.createPathForFolder(videoId), 'infos.json'));
                    for (var j in infosFile) {
                        if (fileservice.exist(infosFile[j])) {
                            infos = fileservice.readJson(infosFile[j]);
                            break;
                        }
                    }
                    result = {videoId: obj.videoId, infos: infos};
                }
                res.send(result);
            } else {
                res.sendStatus(404);
            }
        });


        /**
         *   Get the raw data of the encoded video or an error if the video is not ready
         *
         */
        app.get('/api/encode/raw/:videoid', function (req, res) {
            var videoid = req.params.videoid;
            var zippath = path.join(__dirname,'../..', fileservice.createPathForFolder(videoid), videoid + '.zip');
            fs.exists(zippath, (result) => {
                if (result) {
                    res.sendFile(zippath);
                } else {
                    res.sendStatus(404);
                }
            })
        });

        /**
         *   Get all of the states of all of the videos
         *
         */
        app.get('/api/encode/state', function (req, res) {
            var result = [];
            var videos = fileservice.getFoldersInPath();
            var obj;
            for (var i in videos) {
                obj = fileservice.readJson(fileservice.createPathForFolder(videos[i]) + '/state.json');
                if (Object.keys(obj).length !== 0 || obj.constructor !== Object) {
                    result.push(obj);
                }
            }
            res.send(result);
        });

        /**
         *   Get the state of the specific video defined by videoId
         *
         */
        app.get('/api/encode/state/:videoid', function (req, res) {
            var videoId = req.params.videoid;
            var statePath = fileservice.createPathForFolder(videoId) + '/state.json';
            var result = fileservice.readJson(statePath);
            res.send(result);
        });

        /**
         *   Get the encoding queue
         *
         */
        app.get('/api/encode/queue', function (req, res) {
            var result = queueservice.readQueue();

            res.send(result);
        });

        /**
         * Clean the queue
         *
         */
        app.delete('/api/encode/queue', function (req, res) {
            var result = queueservice.cleanQueue();

            res.send(result);
        });


        /**
         *   Post a video and store them in the filesystem, return the videoId
         *
         */
        app.post('/api/encode', function(req, res) {
            var videoId = fileservice.createUuid();
            var path;
            var encodingList = [];
            var infos = new VideoInfo({videoId: videoId});
            var mimetype = '';
            var extension = "mp4";
            var magic = new Magic(mmm.MAGIC_MIME_TYPE);

            req.pipe(req.busboy);

            // Get and save file
            req.busboy.on('file', function(fieldname, file, filename) {
                path = fileservice.createPathForFolder(videoId);
                fileservice.createPathIfNotExist(path);
                var fstream = fs.createWriteStream(path + '/uploadedfile');
                file.pipe(fstream);
                fstream.on('close', function () {
                    magic.detectFile(path + '/uploadedfile', function(err, result) {
                        if (err) throw err;
                        mimetype = result;
                        extension = mime.extension(mimetype);
                        fileservice.writeJson(path + '/infos.json', infos);
                        fs.renameSync(path + '/uploadedfile', path + '/video.' + extension);
                        if (mimetype.split('/')[0] === 'video') {
                            encodingList = encodingservice.getEncodingParameters();
                            queueservice.saveNewJob(videoId, encodingList);
                        }
                    });
                    res.redirect('back');
                });
            });

            // Get parameters
            req.busboy.on('field', function(fieldname, val, fieldnameTruncated, valTruncated, encoding, mimetype) {
                if (fieldname !== 'videoId' && fieldname !== 'ytb_id') {
                    infos[fieldname] = val;
                }
            });
        });


        /**
         *   Delete a video
         *
         */
        app.delete('/api/encode/:videoid', function (req, res) {
            var videoid = req.params.videoid;
            var folder = path.join(fileservice.getDefaultPath(), videoid);
            if (fileservice.exist(folder)) {
                fileservice.removeFolder(folder);
                res.sendStatus(200);
            } else {
                res.sendStatus(404);
            }
        });

        return app;
    }
};