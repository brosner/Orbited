alert("Local Configuration")
TOP_DOMAIN = "127.0.0.1"
APP_HOSTNAME = "http://127.0.0.1:8000"
ORBIT_HOSTNAME = "http://127.0.0.1:8000"
var pieces = String.split(document.location, '?')
if (pieces.length == 1) {
    CHANNEL = "orbited"
}
else {
    CHANNEL = String.substring(pieces[1], 8)
}

