/**
 * Created by mlacaud on 14/08/17.
 */
var {EncodingParameter} = require('../models/encodingparameter');
var fs = require('fs');
var fileservice = require('../services/files.service');
var encodingservice = require('../services/encoding.service');

module.exports = {
    addApi: function (app) {

        /**
         *   Get a list of the videos on the file system
         *
         */
        app.get('/api/encode', function (req, res) {
            var result = fileservice.getFoldersInPath();
            res.send(result);
        });


        /**
         *   Get the raw data of the encoded video or an error if the video is not ready
         *
         */
        app.get('/api/encode/raw/:videoid', function (req, res) {
            //TODO
            var result = "encode";
            res.send(result);
        });

        /**
         *   Get all of the states of all of the videos
         *
         */
        app.get('/api/encode/state', function (req, res) {
            var result = [];
            var videos = fileservice.getFoldersInPath();
            for (var i in videos) {
                result.push(fileservice.readJson(fileservice.createPathForFolder(videos[i]) + '/state.json'));
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
         *   Post a video and store them in the filesystem, return the videoId
         *
         */
        app.post('/api/encode', function(req, res) {
            var videoId = "default";
            var path;
            var encodingList = [];
            var encodingObject = {};

            req.pipe(req.busboy);

            // Get and save file
            req.busboy.on('file', function(fieldname, file, filename) {
                path = fileservice.createPathForFolder(videoId);
                fileservice.createPathIfNotExist(path);
                var fstream = fs.createWriteStream(path + '/' + filename);
                file.pipe(fstream);
                fstream.on('close', function () {
                    encodingList.push(new EncodingParameter(encodingObject));
                    encodingList.push(new EncodingParameter({}));
                    encodingservice.encodeVideo(videoId, encodingList);
                    res.redirect('back');
                });
            });

            // Get parameters
            req.busboy.on('field', function(fieldname, val, fieldnameTruncated, valTruncated, encoding, mimetype) {
                if(fieldname === "videoId" && val && val !== "") {
                    videoId = val;
                } else {
                    encodingObject[fieldname] = parseInt(val);
                }
            });
        });


        /**
         *   Delete a video
         *
         */
        app.delete('/api/encode/:videoid', function (req, res) {
            //TODO
            var result = "encode";
            res.send(result);
        });

        return app;
    }
};