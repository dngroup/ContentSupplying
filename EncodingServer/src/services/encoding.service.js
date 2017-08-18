const { spawn } = require('child_process');
var filesservice = require('./files.service');
var {EncodingState} = require('../models/encodingstate');

function encodeVideo(videoId, encodingParameters) {
    //Get Path
    var fo = folderObjectCreation(videoId);

    // Init state.json file
    var encodingState = new EncodingState({videoId: videoId});
    filesservice.writeJson(fo.statePath, encodingState);


    // Encode audio
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
            state.percentOfCompletion = Math.floor((taskExecuted / (encodingParameters.length + 2)) * 100);
        } else {
            state.failures.push("audio failed");
        }
        filesservice.writeJson(fo.statePath, state);
        console.log('End of audio encryption, code: ' + code);
        videoEncoding(0, encodingParameters, fo, [dest_audio], taskExecuted);
    });

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
            state.isReady = true;
            state.percentOfCompletion = Math.floor((taskExecuted / (encodingParameters.length + 2)) * 100);
        } else {
            state.failures.push("Segmentation failed");
        }
        filesservice.writeJson(fo.statePath, state);
        console.log('End of segmentation, code: ' + code);
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

    process.on('close', (code) => {
        // State management
        var state = filesservice.readJson(fo.statePath);
        if (code === 0) {
            taskExecuted += 1;
            listOfFiles.push(dest);
            state.availableQualities.push(encodingParameters[currentIndex]);
            state.percentOfCompletion = Math.floor((taskExecuted / (encodingParameters.length + 2)) * 100);
            if (state.availableQualities.length === encodingParameters.length) {
                state.isEncoded = true;
                setTimeout(segmentation, 0, encodingParameters, fo, listOfFiles, taskExecuted);
            }
        } else {
            state.failures.push(encodingParameters[currentIndex]);
        }
        filesservice.writeJson(fo.statePath, state);

        console.log('End of video encryption for parameter ' + currentIndex + ', code: ' + code);

        // Next encoding
        if (currentIndex + 1 < encodingParameters.length) {
            videoEncoding(currentIndex + 1, encodingParameters, taskExecuted);
        }
    });
}

function folderObjectCreation(videoId) {
    var folderPath = filesservice.createPathForFolder(videoId);
    var result = {
        folderPath: folderPath,
        tmpPath: folderPath + '/tmp',
        statePath: folderPath + '/state.json',
        encodedPath: folderPath + '/' + videoId,
        videoPath: folderPath + '/' + filesservice.getVideosInPath(folderPath)[0]
    };
    filesservice.createPathIfNotExist(result.tmpPath);

    return result;
}

module.exports = {
    encodeVideo: encodeVideo
};