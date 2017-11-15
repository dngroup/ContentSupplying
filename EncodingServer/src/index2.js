var express = require('express'),
    cors = require('cors'),
    url = require('url'),
    request = require('request');
const { URL } = require('url');
var app = express();




// Manage CORS
app.use(cors());

// Pipe code for post
var proxy = require('express-http-proxy')
var encoding_server_addr = "http://localhost:8080/";

function sendToEncoding(req, res) {
    var url = new URL(req.url, encoding_server_addr);
    req.pipe(request(url.toString())).pipe(res);
}

app.post('/api/encode', sendToEncoding);


//app.post('/api/encode', proxy('localhost:8080'));


var server = app.listen(8081, function () {
    var host = server.address().address;
    var port = server.address().port;

    console.log("Encoding server listening at http://%s:%s", host, port);
});