var express = require('express'),
    cors = require('cors'),
    url = require('url'),
    api_encoding = require('./handlers/api_content'),
    flagsservice = require('./services/flags.service'),
    encodingservice = require('./services/encoding.service');
var {EncodingParameter} = require('./models/encodingparameter');
var busboy = require('connect-busboy');

var app = express();

app.use(busboy());

// Manage CORS
app.use(cors());

// Manage flags
var flags = flagsservice.manageFlags(process.argv);

// static files
app.use(express.static('static'));


// Add /api/encoding functions
app = api_encoding.addApi(app);


var server = app.listen(flags.port, function () {
    var host = server.address().address;
    var port = server.address().port;

    console.log("Encoding server listening at http://%s:%s", host, port);
});

//encodingservice.segmentation([new EncodingParameter({})], encodingservice.folderObjectCreation('IdTest'), [ './contents/IdTest/tmp/audio.m4a', './contents/IdTest/tmp/video_2000_1080x720_24.mp4' ]);