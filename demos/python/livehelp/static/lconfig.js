alert("Local Configuration")
TOP_DOMAIN = "127.0.0.1"
APP_HOSTNAME = "http://127.0.0.1:8000"
ORBIT_HOSTNAME = "http://"+document.location.toString().split('/')[2]
var pieces = document.location.toString().split('?')
if (pieces.length == 1) {
    CHANNEL = "orbited"
}
else {
    CHANNEL = pieces[1].substring(8)
}

