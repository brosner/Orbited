TOP_DOMAIN = "orbited.org"
APP_HOSTNAME = "http://orbited.org/livehelp"
ORBIT_HOSTNAME = "http://orbited.org:8000"
var pieces = String.split(document.location, '?')
if (pieces.length == 1) {
    CHANNEL = "orbited"
}
else {
    CHANNEL = String.substring(pieces[1], 8)
}

