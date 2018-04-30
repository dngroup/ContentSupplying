var playerService = (function() {
    var player;
    return {
        initPlayer: function () {
            player = dashjs.MediaPlayer().create();
            player.getDebug().setLogToBrowserConsole(false);
            player.initialize();
            player.attachView(document.getElementById('videoplayer'));
            player.attachVideoContainer(document.getElementById('videocontainer'));
            player.setAutoSwitchQuality(true);
            player.setABRStrategy("abrThroughput");
        },
        startPlayer: function (url) {
            player.setAutoPlay(true);
            player.attachSource(url);
        }
    }
})