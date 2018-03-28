#!/usr/bin/env node

var amqp = require('amqplib/callback_api');

amqp.connect('amqp://localhost:5672', function(err, conn) {
    conn.createChannel(function(err, ch) {
        var q = 'video';
        var object = {
            uuid: "uuid",
            title: "title",
            description: "description",
            author: "author",
            thumbnail: "thumbnail",
            type: "vod",
            source_path: "sourcepath",
            encoded_path: "encoded_path",
            encoding_status: "to_encode", //['to_encode', 'encoding', 'encoded', 'to_stop', 'stopped', 'error']
            created_at: new Date(),
            updated_at: null,
            category: {},
            client: {},
            user: {},
            representations: [{
                fps: 24,
                segment_duration: 6,
                gop_size: 12,
                resolutions: [{
                    width: 1920,
                    height: 1080,
                    bitrates: [{
                        bitrate: 400
                    }, {
                        bitrate: 2000
                    }, {
                        bitrate: 4000
                    }]
                }]
            }]
        };

        var msg = JSON.stringify(object);

        ch.assertQueue(q, {durable: true});

        ch.sendToQueue(q, new Buffer(msg), {persitent: true});
        console.log(" [x] Sent %s", msg);
    });
    setTimeout(function() { conn.close(); process.exit(0) }, 500);
});