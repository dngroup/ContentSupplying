/**
 * Created by mlacaud on 21/08/17.
 */
/**
 *  VideoInfo
 *
 * {string} ytb_id
 * {string} title
 * {string} description
 * {string} author
 *
 */
class VideoInfo {
    constructor(obj) {
        var defaultYtbId = "default";
        var defaultTitle = "title";
        var defaultDescription = "Video description.";
        var defaultAuthor = "JOADA";

        this.ytb_id = obj.ytb_id || obj.videoId || defaultYtbId;
        this.title = obj.title || obj.videoname || defaultTitle;
        this.description = obj.description || defaultDescription;
        this.author = obj.author || defaultAuthor;
    }
}

exports.VideoInfo = VideoInfo;