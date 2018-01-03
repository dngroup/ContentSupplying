const { spawn } = require('child_process');
var filesservice = require('./files.service');
var archiverservice = require('./archiver.service');
var {EncodingState} = require('../models/encodingstate');
var {EncodingParameter} = require('../models/encodingparameter');
var {FolderPath} = require('../models/folderpath');
var path = require('path');

var extraTasks = 3;

function encodeVideo(videoId, encodingParameters) {
    //Get Path
    var fo = folderObjectCreation(videoId);

    // Init state.json file
    var encodingState = new EncodingState({videoId: videoId});
    filesservice.writeJson(fo.statePath, encodingState);



    var dest_audio = fo.tmpPath + '/audio.m4a';
    var process_audio = spawn('ffmpeg', ['-y', '-i', fo.videoPath,
        "-map", "0:a", "-c:a", "aac",
        "-strict", "-2", "-force_key_frames", "expr:gte(t,n_forced*0.5)",
        dest_audio]);
    process_audio.on('close', (code) => {
        var state = filesservice.readJson(fo.statePath);
        var taskExecuted = 0;
        if (code === 0) {
            taskExecuted = 1;
            state.isAudioReady = true;
            state.percentOfCompletion = Math.floor((taskExecuted / (encodingParameters.length + extraTasks)) * 100);
        } else {
            state.failures.push("audio failed");
        }
        filesservice.writeJson(fo.statePath, state);
        videoEncoding(0, encodingParameters, fo, [dest_audio], taskExecuted);
    });

    getDuration(fo);
}


function segmentation(encodingParameters, fo, listOfFiles, taskExecuted) {
    var duration = encodingParameters[0].segmentDuration * 1000;
    var destMPD = fo.encodedPath + "/mpd.mpd";
    filesservice.createPathIfNotExist(fo.encodedPath);
    var args = ["-dash", duration, "-profile", "live", "-bs-switching", "no", "-segment-name",
        "$Bandwidth$/out$Bandwidth$_dash$Number$", "-out", destMPD].concat(listOfFiles);

    var process = spawn("MP4Box", args);

    process.on('close', (code) => {
        var state = filesservice.readJson(fo.statePath);
        if (code === 0) {
            taskExecuted += 1;
            state.percentOfCompletion = Math.floor((taskExecuted / (encodingParameters.length + extraTasks)) * 100);

        } else {
            state.failures.push("Segmentation failed");
        }
        filesservice.writeJson(fo.statePath, state);

        moveInfos(fo);
        archiveEncodedVideo(fo, encodingParameters, taskExecuted);
    });
}

function archiveEncodedVideo(fo, encodingParameters, taskExecuted) {
    var queueservice = require('./queue.service');
    var state = filesservice.readJson(fo.statePath);
    archiverservice.archiveVideoFiles(fo).then(() => {
        taskExecuted += 1;
        state.percentOfCompletion = Math.floor((taskExecuted / (encodingParameters.length + extraTasks)) * 100);
        state.isReady = true;
        filesservice.writeJson(fo.statePath, state);
        queueservice.removeFromQueue(fo.videoId);
    }).catch(() => {
        state.failures.push("Archiving failed");
        filesservice.writeJson(fo.statePath, state);
        queueservice.removeFromQueue(fo.videoId);
    });

}

function moveInfos(fo) {
    // Move infos
    var infos = filesservice.readJson(fo.folderPath + '/infos.json');
    filesservice.writeJson(fo.encodedPath + '/infos.json', infos);
    filesservice.removeFile(fo.folderPath + '/infos.json');
    filesservice.removeFolder(fo.tmpPath);
}

function thumbnail(fo) {
    filesservice.createPathIfNotExist(fo.encodedPath);
    var process = spawn('ffmpeg', ['-y', '-i', fo.videoPath,
    '-vf', 'thumbnail,scale=384:192', '-frames:v','1', fo.thumbnailPath]);
}

function removeFirstStrangeGoP(fo) {
    var process = spawn('ffmpeg', ['-y', '-f h264', '-i', fo.videoPath,
        '-ss', '0.5', '-vcodec', 'copy', fo.videoPath]);
}

function getDuration(fo) {
    var process = spawn('ffprobe', [ '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', fo.videoPath]);

    process.stdout.on('data', (data) => {
        var infos = filesservice.readJson(path.join(fo.folderPath, 'infos.json'));
        infos.duration = Math.floor(parseInt(data));
        filesservice.writeJson(path.join(fo.folderPath, 'infos.json'), infos);
    });
}

function videoEncoding(currentIndex, encodingParameters, fo, listOfFiles, taskExecuted) {
    var dest = fo.tmpPath + '/video_' + encodingParameters[currentIndex].bitrate + '_' + encodingParameters[currentIndex].width + "x" +
        encodingParameters[currentIndex].height + '_' + encodingParameters[currentIndex].fps + '.mp4';
    var process = spawn('ffmpeg', ['-y', '-i', fo.videoPath,
        "-map", "0:v", "-c:v", "libx264",
        "-b:v", encodingParameters[currentIndex].bitrate + "k",
        "-vf", "scale=" + encodingParameters[currentIndex].width + ":" + encodingParameters[currentIndex].height,
        "-r", encodingParameters[currentIndex].fps,
        "-x264opts", "keyint=" + encodingParameters[currentIndex].gopSize + ":min-keyint=1:scenecut=-1",
        dest]);

    if (currentIndex === 0) {
        thumbnail(fo);
    }

    process.on('close', (code) => {
        // State management
        var state = filesservice.readJson(fo.statePath);
        if (code === 0) {
            taskExecuted += 1;
            listOfFiles.push(dest);
            state.availableQualities.push(encodingParameters[currentIndex]);
            state.percentOfCompletion = Math.floor((taskExecuted / (encodingParameters.length + extraTasks)) * 100);
            if (state.availableQualities.length === encodingParameters.length) {
                state.isEncoded = true;
                setTimeout(segmentation, 0, encodingParameters, fo, listOfFiles, taskExecuted);
            }
        } else {
            state.failures.push(encodingParameters[currentIndex]);
        }
        filesservice.writeJson(fo.statePath, state);

        // Next encoding
        if (currentIndex + 1 < encodingParameters.length) {
            var newIndex = currentIndex + 1;
            videoEncoding(newIndex, encodingParameters, fo, listOfFiles, taskExecuted);
        }
    });

    /*process.stdout.on('data', (data) => {
        console.log(`stdout: ${data}`);
    });

    process.stderr.on('data', (data) => {
        console.log(`stderr: ${data}`);
    });*/
}

function getEncodingParameters() {
    var objs = [
        {
            bitrate: 500,
            width: 1280,
            height: 720
        },
        {
        bitrate: 1200,
        width: 1280,
        height: 720
    }
        /*{
            bitrate: 500,
            width: 848,
            height: 480
        },
        {
        bitrate: 1200,
        width: 848,
        height: 480
    }*//*,{
        bitrate: 3000,
        width: 1280,
        height: 720
    },{
        bitrate: 5000,
        width: 1920,
        height: 1080
    }*/];

    var result = [];
    for (var i = 0; i < objs.length; i++) {
        result.push(new EncodingParameter(objs[i]));
    }

    return result;
}

function folderObjectCreation(videoId) {
    var obj = {
        videoId: videoId
    };
    var result = new FolderPath(obj);
    filesservice.createPathIfNotExist(result.tmpPath);

    return result;
}

module.exports = {
    encodeVideo: encodeVideo,
    getEncodingParameters: getEncodingParameters
};