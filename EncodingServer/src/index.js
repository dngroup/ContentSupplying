var express = require('express'),
    cors = require('cors'),
    url = require('url'),
    http = require('http'),
    fs = require('fs'),
    api_encoding = require('./handlers/api_content'),
    rabbithandler = require('./handlers/rabbithandler'),
    flagsservice = require('./services/flags.service'),
    queueservice = require('./services/queue.service');
var { EncodingParameter } = require('./models/encodingparameter');
var { FolderPath } = require('./models/folderpath');
var busboy = require('connect-busboy');
var amqp = require('amqplib/callback_api');


// Manage flags
var flags = flagsservice.manageFlags(process.argv);

if (!flags.broker) {
    var app = express();

    app.use(busboy());

    // Manage CORS
    app.use(cors());
    // static files
    app.use(express.static('static'));


    // Add /api/encoding functions
    app = api_encoding.addApi(app);


    queueservice.cleanQueue();
    queueservice.startWatcher();

    var server = app.listen(flags.port, function () {
        var host = server.address().address;
        var port = server.address().port;

        console.log("Encoding server listening at http://%s:%s", host, port);
    });


    //archiverservice.archiveVideoFiles(new FolderPath({videoId:'IdTest'})).then(() => console.log('Encoding Terminé !'));
    //archiverservice.archiveVideoFiles(new FolderPath({videoId:'IdTest'})).then(() => console.log('Encoding 2 Terminé !'));
    //encodingservice.segmentation([new EncodingParameter({})], encodingservice.folderObjectCreation('IdTest'), [ './contents/IdTest/tmp/audio.m4a', './contents/IdTest/tmp/video_2000_1080x720_24.mp4' ]);

} else {

    amqp.connect('amqp://guest:guest@' + flags.broker, rabbithandler.RabbitHandle);
}