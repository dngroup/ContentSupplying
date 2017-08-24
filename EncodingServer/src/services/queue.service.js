var filesservice = require('./files.service');
var encodingservice = require('./encoding.service');
var {EncodingQueue} = require('../models/encodingqueue');

var interval;
var jobtime = 5000;
var parallelJob = 1;

function startWatcher() {
    if (!interval) {
        interval = setInterval(startJob, jobtime);
    }
}

function startJob() {
    var queueFile = filesservice.getDefaultPath() + '/queue.json';
    filesservice.createPathIfNotExist(filesservice.getDefaultPath());
    var queue = filesservice.readJson(queueFile);
    var runningJob = 0;
    if (queue && queue.length > 0) {
        for (var i = 0; i < queue.length; i++) {
            if (queue[i].isRunning) {
                runningJob += 1;
                if (runningJob >= parallelJob) {
                    break;
                }
            }
        }

        if (runningJob < parallelJob) {
            queue[0].isRunning = true;
            filesservice.writeJson(queueFile, queue);
            encodingservice.encodeVideo(queue[0].videoId, queue[0].encodingParameters);
        }
    }
}

function saveNewJob(videoId, encodingParameters) {
    var queueFile = filesservice.getDefaultPath() + '/queue.json';
    filesservice.createPathIfNotExist(filesservice.getDefaultPath());
    var queue = filesservice.readJson(queueFile);
    var obj = {
        videoId: videoId,
        encodingParameters: encodingParameters
    };

    if (queue.constructor === Object) {
        queue = [];
    }

    queue.push(new EncodingQueue(obj));
    filesservice.writeJson(queueFile, queue);
}

function removeFromQueue(videoId) {
    var queueFile = filesservice.getDefaultPath() + '/queue.json';
    filesservice.createPathIfNotExist(filesservice.getDefaultPath());
    var queue = filesservice.readJson(queueFile);
    for (var i = 0; i < queue.length; i++) {
        if (queue[i].videoId === videoId && queue[i].isRunning === true) {
            console.log("removing");
            queue.splice(i,1);
        }
    }
    filesservice.writeJson(queueFile, queue);
}

function readQueue() {
    var queueFile = filesservice.getDefaultPath() + '/queue.json';
    filesservice.createPathIfNotExist(filesservice.getDefaultPath());
    var queue = filesservice.readJson(queueFile);

    if (queue.constructor === Object) {
        queue = [];
    }

    return queue;
}

function cleanQueue() {
    var queueFile = filesservice.getDefaultPath() + '/queue.json';
    filesservice.createPathIfNotExist(filesservice.getDefaultPath());
    var queue = [];
    filesservice.writeJson(queueFile, queue);
    return queue;
}


module.exports = {
    startWatcher: startWatcher,
    saveNewJob: saveNewJob,
    removeFromQueue: removeFromQueue,
    readQueue: readQueue,
    cleanQueue: cleanQueue
};