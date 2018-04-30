
/**
 *   EncodingState
 *
 *   {string} videoId
 *   {boolean} isReady // When the full encoding process is over
 *   {boolean} isAudioReady // When the audio is encoded
 *   {boolean} isEncoded // When the video are encoded in every quality /!\ that does not mean the full encoding process is over
 *   {[]EncodingParameters} availableQualities // All the EncodingParameters that are already encoded in the process
 *   {number} percentOfCompletion // Percent Of completion according to the number of tasks /!\ this parameter can not be used to provide a good estimation of the time needed to finish the encoding process
 *   {[]Obj} failures // All the tasks that have thrown an error
 */

class EncodingState {

    constructor(obj){
        var defaultVideoId = "Default";
        var defaultIsReady = false;
        var defaultIsAudioReady = false;
        var defaultIsEncoded = false;
        var defaultAvailableQualities = [];
        var defaultPercentOfCompletion = 0;
        var defaultFailures = [];

        this.videoId = obj.videoId || defaultVideoId;
        this.isReady = obj.isReady || defaultIsReady;
        this.isAudioReady = obj.isAudioReady || defaultIsAudioReady;
        this.isEncoded = obj.isEncoded || defaultIsEncoded;
        this.availableQualities = obj.availableQualities || defaultAvailableQualities;
        this.percentOfCompletion = obj.percentOfCompletion || defaultPercentOfCompletion;
        this.failures = obj.failures || defaultFailures;
    }


}

exports.EncodingState = EncodingState;