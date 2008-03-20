TOP_DOMAIN = "orbited.org"
APP_HOSTNAME = "http://orbited.org/livehelp"
ORBIT_HOSTNAME = "http://orbited.org:8000"
try {
    CHANNEL = String.substring(String.split(document.location, '?')[1], 8)
}
catch (e) {
    CHANNEL = "orbited"
}

