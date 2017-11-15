var playerservice = playerService();

new Vue({
    el: '#app',
    data: {
        greeting: 'Le meilleur frontend du monde',
        backendurl: null,
        listVideo: [],
        isInitial: true,
        isSaving: false,
        uploadFieldName: '',
        updateTime: null
    },
    mounted: function () {
        playerservice.initPlayer();
        axios.get("/api/backend").then((rep) => {
            this.backendurl = rep.data;
            this.getListCurrentVideos();
            setTimeout(this.getListCurrentVideos, 5000);
        }).catch((e) => console.log(e))
    },
    methods: {
        humanizeURL: function (url) {
            return url
                .replace(/^https?:\/\//, '')
                .replace(/\/$/, '')
        },
        getListCurrentVideos() {
            axios.get(this.backendurl + "/content").then((rep)=> {
                this.listVideo = rep.data;
                this.updateTime = new Date();
            }).catch((e) => console.log(e))
        },
        filesChange(filename, file) {
            this.isInitial = false;
            this.isSaving = true;
            var formData = new FormData();
            formData.append("trailer", file[0], file[0].name)
            axios.post(this.backendurl + "/content/trailer", formData).then(x => console.log("POST"));
        },
        onPlay(video) {
            playerservice.startPlayer(this.backendurl + "/video/" + video.Name + "/mpd.mpd");
        }
    }
})