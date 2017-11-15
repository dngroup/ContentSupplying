const express = require('express')
const app = express()

if(process.argv.length != 3) {
console.log("USAGE: node index.js SERVERADDRESS")
process.exit()
}
app.use(express.static('static'));

app.get('/api/backend', function (req, res) {
  res.send(process.argv[2])
})

app.listen(3000, function () {
  console.log('Frontend listening on port 3000')
})

