/**
 * Created by mlacaud on 14/08/17.
 */

module.exports = {
    manageFlags: function(argv) {
        var flags = {
            port: 8080
        };

        for(var i=0; i<argv.length; i++) {
            switch (argv[i]) {
                case "-p":
                    flags.port = argv[i+1] || flags.port;
                    break;
                default:
                    break;
            }
        }

        return flags;
    }
};