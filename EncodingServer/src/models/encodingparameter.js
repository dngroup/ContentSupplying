var defaultBitrate = 2000;
var defaultWidth = 720;
var defaultHeight = 480;
var defaultFps = 24;
var defaultSegmentDuration = 6;
var defaultGopSize = 12;

/**
* Parameters for encoding
*
*   {number} bitrate
*   {number} width
*   {number} height
*   {number} fps
*   {number} segmentDuration
*   {number} gopSize
*
*/
class EncodingParameter {
    constructor(obj){
        this.bitrate = obj.bitrate || defaultBitrate;
        this.width = obj.width || defaultWidth;
        this.height = obj.height || defaultHeight;
        this.fps = obj.fps || defaultFps;
        this.segmentDuration = obj.segmentDuration || defaultSegmentDuration;
        this.gopSize = obj.gopSize || defaultGopSize;
    }

}

exports.EncodingParameter = EncodingParameter;