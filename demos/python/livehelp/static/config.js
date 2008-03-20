TOP_DOMAIN = "orbited.org"
APP_HOSTNAME = "http://orbited.org/livehelp"
ORBIT_HOSTNAME = "http://"+document.location.toString().split('/')[2]
var pieces = document.location.toString().split('?')
if (pieces.length == 1) {
    CHANNEL = "orbited"
}
else {
    CHANNEL = pieces[1].substring(8)
}

