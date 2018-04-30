var {EncodingParameter} = require('../models/encodingparameter');
var {VideoInfo} = require('../models/videoinfo');
var fs = require('fs');
var http = require('http');
var fileservice = require('../services/files.service');
var encodingservice = require('../services/encoding.service');
var queueservice = require('../services/queue.service');
var path = require('path');
var mmm = require('mmmagic');
var {Magic} = require('mmmagic');
var mime = require('mime-types');
var path = require('path');

var channel;

brokerEncodingHandler = function(msg) {
    var secs = msg.content.toString().split('.').length - 1;
    var json = JSON.parse(msg.content.toString());
    var infos = json.infos || {};
    
    console.log(" [x] Received");

    // Get file
    var path = fileservice.createPathForFolder(json.id);
    fileservice.createPathIfNotExist(path);
    var file = fs.createWriteStream(path + '/uploadedfile');
    var request = http.get(json.videoUrl, function(response) {
      response.pipe(file);
    });
    //test file
    var magic = new Magic(mmm.MAGIC_MIME_TYPE);
    magic.detectFile(path + '/uploadedfile', function(err, result) {
        //Interval for answer
        var interval = setInterval(function() {
            if (queueservice.isJobOverForId(json.id)) {
                clearInterval(interval);
                console.log(" [x] Done");
                channel.ack(msg);
            }
        }, secs * 1000);
        console.log(result);
        //Rewrite with correct mimetype
        if (err) throw err;
        mimetype = result;
        extension = mime.extension(mimetype);
        fileservice.writeJson(path + '/infos.json', infos);
        fs.renameSync(path + '/uploadedfile', path + '/video.' + extension);
        if (mimetype.split('/')[0] === 'video') {
            // Test if encoding parameters are present
            if (Object.keys(json.encodingParameters).length === 0 && json.encodingParameters.constructor === Object) {
                json.encodingParameters = encodingservice.getEncodingParameters();
            }
            //start encoding
            queueservice.saveNewJob(json.id, json.encodingParameters);
        }
    });


  };

brokerEncodingHandler2 = function(msg) {
    var json = JSON.parse(msg.content.toString());
    console.log(json);
    setTimeout(() => {channel.ack(msg);}, 10000);


};

RabbitHandle = function(err, conn) {
    conn.createChannel(function(err, ch) {
      var q = 'video';
      
      ch.assertQueue(q, {durable: true});
      ch.prefetch(1);
      console.log(" [*] Waiting for messages in %s. To exit press CTRL+C", q);

      // New message received
      channel = ch;
      ch.consume(q, brokerEncodingHandler2, {noAck: false});
    });
  }

  module.exports = {
      RabbitHandle: RabbitHandle
  }