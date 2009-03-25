from twisted.web import resource, error
from orbited.config import map as config
from orbited import logging
import urlparse

class MonitorResource(resource.Resource):
    def render(self, request):
        monitoring = config['globalVars']['monitoring']
        body = "<body><h2>Orbited.system.monitor</h2>"
        if monitoring:
            head = """
        <head>
            <script src='/static/Orbited.js'></script>
            <script>
                window.onload = function() {
                    var display = document.getElementById('display');
                    var dMap = {};
                    var c = new Orbited.TCPSocket();
                    c.onclose = function() {
                        document.write('connection to server lost');
                    }
                    var process = function(frame) {
                        var name = frame[0];
                        var data = frame[1];
                        if (name == "INIT") {
                            display.innerHTML = '';
                            dMap = {};
                            var rTop = document.createElement('tr');
                            var rBottom = document.createElement('tr');
                            for (var i = 0; i < data.length; i++) {
                                var dTop = document.createElement('td');
                                var dBottom = document.createElement('td');
                                dTop.innerHTML = data[i];
                                dMap[data[i]] = dBottom;
                                rTop.appendChild(dTop);
                                rBottom.appendChild(dBottom);
                            }
                            display.appendChild(rTop);
                            display.appendChild(rBottom);
                        }
                        else if (name == "UPDATE") {
                            for (item in data) {
                                dMap[item].innerHTML = data[item];
                            }
                        }
                        else {
                            alert('invalid frame:'+frame);
                        }
                    }
                    c.onread = function(data) {
                        var frames = data.split('~');
                        for (var i = 0; i < frames.length-1; i++) {
                            process(eval("("+frames[i]+")"));
                        }
                    }
                    c.open(Orbited.settings.hostname, %s);
                }
            </script>
        </head>
        """%(monitoring,)
            body += "<table id=display border=1></table>"
        else:
            head = "<head></head>"
        body += "<br>&lt; <a href='/system'>Orbited.system</a>"
        body += "</body></html>"
        return "<html>" + head + body + "</html"