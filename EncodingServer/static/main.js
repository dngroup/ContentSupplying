new Vue({
    el: '#app',
    data: {
        greeting: 'Best frontend ever',
        uploadFieldName: '',
        backendurl: "",
        params: {
            videoId: "test",
            description: "ma super description",
            number: 45,
            boolean: true,
            test: {
                test1: "test1",
                test2: "test2"
            }
        }
    },
    mounted: function () {

    },
    methods: {
        humanizeURL: function (url) {
            return url
                .replace(/^https?:\/\//, '')
                .replace(/\/$/, '')
        },
        filesChange(filename, file) {
            var formData = new FormData();
            for(i in this.params) {
                if (this.params[i] !== null && typeof this.params[i] === 'object') {
                    formData.append(i, JSON.stringify(this.params[i]));
                } else {
                    formData.append(i, this.params[i]);
                }
            }
            formData.append("trailer", file[0], file[0].name)
            axios.post(this.backendurl + "/api/encode", formData).then(x => console.log("POST"));
        }
    }
})