alert("Local Configuration")
TOP_DOMAIN = "127.0.0.1"
APP_HOSTNAME = "http://127.0.0.1:8000"
ORBIT_HOSTNAME = "http://127.0.0.1:8000"
try {
    CHANNEL = String.substring(String.split(document.location, '?')[1], 8)
}
catch (e) {
    CHANNEL = "orbited"
}

