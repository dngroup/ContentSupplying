/**
 * Created by mlacaud on 24/08/17.
 */

var defaultVideoId = 'default';
var defaultIsRunning = false;
var defaultEncodingParameters = [];


/**
 *  EncodingQueue
 *
 *   {string} videoId
 *   {boolean} isRunning
 *   {[]EncodingParameter} encodingParameters
 *
 */
class EncodingQueue {
    constructor(obj){
        this.videoId = obj.videoId || defaultVideoId;
        this.isRunning = obj.isRunning || defaultIsRunning;
        this.encodingParameters = obj.encodingParameters || defaultEncodingParameters;
    }

}

exports.EncodingQueue = EncodingQueue;