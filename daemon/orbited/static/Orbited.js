// NOTE: to log/debug with Orbited, there are two methods:
//          Use firebug 
//              1) include Orbited.js (and not Log4js)
//              2) Orbited.loggers[LOGGERNAME].enabled = true
//              And it should do logging for that logger
//          Use log4js
//              1) include log4js.js BEFORE including Orbited.js
//              2) Orbited.loggers[LOGGERNAME].setLevel(Log4js.Level.ALL)
//              3) Orbited.loggers[LOGGERNAME].addAppender(new Log4js.ConsoleAppender())
//              Note: Other levels and appenders can be set as well (see Log4js docs)
//
//       When you are making a call to the logger, prefix the line (first three
//       Characters) with ;;; which we will strip out at build time. So if you
//       have an if statement thats logging specific, start that line with ;;;
//       as well. If you do a try/catch thats specific to logging, prefix all
//       lines involved with ;;;. You'll want to put the try closing } and the
//       catch statement on the same line, or this won't work.
//
//       the logging functions (info, warn, debug, error, etc.) take any number
//       of arguments, like in firebug. If you're using firebug for the logging,
//       you'll actually be able to inspect the objects that you log. Therefore
//       don't do logger.debug(obj1 + " -> " + obj2); as this will convert both
//       objects to strings and not allow you to inspect them in firebug. 
//       Instead call logger.debug(obj1, "->" obj2); Of course, for the Log4js
//       back-end, it will still toString the objects.

(function() {


var HANDSHAKE_TIMEOUT = 30000
var RETRY_INTERVAL = 250
var RETRY_TIMEOUT = 30000

Orbited = {}

Orbited.settings = {}
Orbited.settings.hostname = document.domain
Orbited.settings.port = (location.port.length > 0) ? location.port : 80
Orbited.settings.protocol = 'http'
Orbited.settings.log = false;
Orbited.settings.HEARTBEAT_TIMEOUT = 6000
Orbited.singleton = {}


// Orbited CometSession Errors
Orbited.Errors = {}
Orbited.Errors.ConnectionTimeout = 101
Orbited.Errors.InvalidHandshake = 102
Orbited.Errors.UserConnectionReset = 103

Orbited.Statuses = {}
Orbited.Statuses.ServerClosedConnection = 201


Orbited.util = {}

Orbited.util.browser = null;
if (typeof(ActiveXObject) != "undefined") {
    Orbited.util.browser = 'ie'
} else if (navigator.product == 'Gecko' && window.find && !navigator.savePreferences) {
    Orbited.util.browser = 'firefox'
} else if((typeof window.addEventStream) === 'function') {
    Orbited.util.browser = 'opera'
} 


////
// NB: Base64 code was borrowed from Dojo; we had to fix decode for not
//     striping NULs though.  Tom Trenka from Dojo wont fix this because
//     he claims it helped to detect and avoid broken encoded data.
//     See http://svn.dojotoolkit.org/src/dojox/trunk/encoding/base64.js
//     See http://bugs.dojotoolkit.org/ticket/7400
(function(){
    Orbited.base64 = {};

    var p = "=";
    var tab = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";

    Orbited.base64.encode=function(/* byte[] */ba){
        //  summary
        //  Encode an array of bytes as a base64-encoded string
        var s=[], l=ba.length;
        var rm=l%3;
        var x=l-rm;
        for (var i=0; i<x;){
            var t=ba[i++]<<16|ba[i++]<<8|ba[i++];
            s.push(tab.charAt((t>>>18)&0x3f)); 
            s.push(tab.charAt((t>>>12)&0x3f));
            s.push(tab.charAt((t>>>6)&0x3f));
            s.push(tab.charAt(t&0x3f));
        }
        //  deal with trailers, based on patch from Peter Wood.
        switch(rm){
            case 2:{
                var t=ba[i++]<<16|ba[i++]<<8;
                s.push(tab.charAt((t>>>18)&0x3f));
                s.push(tab.charAt((t>>>12)&0x3f));
                s.push(tab.charAt((t>>>6)&0x3f));
                s.push(p);
                break;
            }
            case 1:{
                var t=ba[i++]<<16;
                s.push(tab.charAt((t>>>18)&0x3f));
                s.push(tab.charAt((t>>>12)&0x3f));
                s.push(p);
                s.push(p);
                break;
            }
        }
        return s.join("");  //  string
    };

    Orbited.base64.decode=function(/* string */str){
        //  summary
        //  Convert a base64-encoded string to an array of bytes
        var s=str.split(""), out=[];
        var l=s.length;
        var tl=0;
        while(s[--l]==p){ ++tl; }   //  strip off trailing padding
        for (var i=0; i<l;){
            var t=tab.indexOf(s[i++])<<18;
            if(i<=l){ t|=tab.indexOf(s[i++])<<12 };
            if(i<=l){ t|=tab.indexOf(s[i++])<<6 };
            if(i<=l){ t|=tab.indexOf(s[i++]) };
            out.push((t>>>16)&0xff);
            out.push((t>>>8)&0xff);
            out.push(t&0xff);
        }
        // strip off trailing padding
        while(tl--){ out.pop(); }
        return out; //  byte[]
    };
})();




Orbited.loggers = {}
Orbited.Loggers = {}
Orbited.util.loggingSystem = null;

if (window.Log4js) {
    Orbited.util.loggingSystem = 'log4js';
}
else if (window.console && console.log) {
    Orbited.util.loggingSystem = 'firebug';
}

Orbited.getLogger = function(name) {
    if (!Orbited.loggers[name]) {
        var logger = null;
        switch (Orbited.util.loggingSystem) {
            case 'firebug':
                logger = new Orbited.Loggers.FirebugLogger(name)
                break;
            case 'log4js':
                logger = new Orbited.Loggers.Log4jsLogger(name)
                break;

            default:
                logger = new Orbited.Loggers.EmptyLogger(name);
                break;
        }
        Orbited.loggers[name] = logger;
    }
    return Orbited.loggers[name]
}

// TODO: is it confusing to have Orbited.Loggers be the various logging classes
//       and Orbited.loggers be actual instances of logging classes?

Orbited.Loggers.FirebugLogger = function(name) {
    var self = this;
    self.name = name;
    self.enabled = false;
    var padArgs = function(args) {
        var newArgs = [ name + ":" ]
        for (var i = 0; i < args.length; ++i) {
            newArgs.push(args[i]);
        }
        return newArgs
    }
    self.log = function() {
        if (!self.enabled) { return }
        console.log.apply(this, padArgs(arguments))
    }
    self.debug = function() {
        if (!self.enabled) { return }
        console.debug.apply(this, padArgs(arguments))
    }
    self.info = function() {
        if (!self.enabled) { return }
        console.info.apply(this, padArgs(arguments))
    }
    self.warn = function() {
        if (!self.enabled) { return }
        console.warn.apply(this, padArgs(arguments))
    }    
    self.error = function() {
        if (!self.enabled) { return }
        console.error.apply(this, padArgs(arguments))
    }
    self.assert = function() {
        if (!self.enabled) { return }
        console.assert.apply(this, padArgs(arguments))
    }
    self.trace = function() {
        if (!self.enabled) { return }
        console.trace.apply(this, padArgs(arguments))
    }
}

Orbited.Loggers.EmptyLogger = function(name) {
    var self = this;
    self.name = name;
    self.log = function() {
    }
    self.debug = function() {
    }
    self.info = function() {
    }
    self.warn = function() {
    }    
    self.error = function() {
    }
    self.assert = function() {
    }
    self.trace = function() {
    }
}


Orbited.Loggers.Log4jsLogger = function(name) {
    var self = this;
    self.name = name;
    // NOTE: Why oh WHY doesn't Log4js accept dots in the logger names, and 
    //       more importantly, why don't they have reasonble error messages?!
    var log4jsName = name
    while (log4jsName.indexOf('.') != -1) {
        log4jsName = log4jsName.replace('.', '_')
    }
    var logger = Log4js.getLogger(log4jsName)
    self.logger = logger
    logger.setLevel(Log4js.Level.OFF)

    var generateOutput = function(args) {
        var newArgs = [ name + ":" ]
        for (var i = 0; i < args.length; ++i) {
            newArgs.push(args[i]);
        }
        return newArgs.join(" ")
    }

    self.setLevel = function(level) {
        logger.setLevel(level)
    }
    self.addAppender = function(a) {
        logger.addAppender(a);
    }
    self.log= function() {
        // NOTE: log doesn't mean anything in Log4js. mapping it to info
        logger.info(generateOutput(arguments));
    }
    self.debug = function() {
        logger.debug(generateOutput(arguments));
    }
    self.info = function() {
        logger.info(generateOutput(arguments));
    }
    self.warn = function() {
        logger.warn(generateOutput(arguments));
    }    
    self.error = function() {
        logger.error(generateOutput(arguments));
    }
    self.assert = function() {
    }
    self.trace = function() {
    }

}
Orbited.system = Orbited.getLogger('system')



Orbited.CometTransports = {}

Orbited.util.chooseTransport = function() {
    var choices = []
    for (var name in Orbited.CometTransports) {
        var transport = Orbited.CometTransports[name];
        if (typeof(transport[Orbited.util.browser]) == "number") {
            Orbited.system.log('viable transport: ', name)
            choices.push(transport)
        }
    }
    // TODO: sort the choices by the values of transport[Orbited.util.browser]
    //       and return the transport with the highest value.
//    return XHRStream
    return choices[0]
}



var createXHR = function () {
    try { return new XMLHttpRequest(); } catch(e) {}
    try { return new ActiveXObject('MSXML3.XMLHTTP'); } catch(e) {}
    try { return new ActiveXObject('MSXML2.XMLHTTP.3.0'); } catch(e) {}
    try { return new ActiveXObject('Msxml2.XMLHTTP'); } catch(e) {}
    try { return new ActiveXObject('Microsoft.XMLHTTP'); } catch(e) {}
    throw new Error('Could not find XMLHttpRequest or an alternative.');
}




Orbited.CometSession = function() {
    var self = this;
    self.readyState = self.READY_STATE_INITIALIZED;
    self.onopen = function() {}
    self.onread = function() {}
    self.onclose = function() {}
    var sessionUrl = null;
    var sessionKey = null;
    var sendQueue = []
    var packetCount = 0;
    var xhr = null;
    var handshakeTimer = null;
    var cometTransport = null;
    var lastPacketId = 0
    var sending = false;

    /*
     * self.open can only be used when readyState is INITIALIZED. Immediately
     * following a call to self.open, the readyState will be OPENING until a
     * connection with the server has been negotiated. self.open takes a url
     * as a single argument which desiginates the remote url with which to
     * establish the connection.
     */
    self.open = function(_url) {
        self.readyState = self.READY_STATE_OPENING;
        xhr = createXHR();
        xhr.open('GET', _url, true);
        xhr.onreadystatechange = function() {
            if (xhr.readyState == 4) {
                if (xhr.status == 200) {
                    sessionKey = xhr.responseText;
;;;                 self.logger.debug('session key is: ', sessionKey)
                    sessionUrl = new Orbited.URL(_url)
                    // START new URL way
//                    sessionUrl.extendPath(sessionKey)
                    // END: new URL way

                    // START: old URL way
                    if (sessionUrl.path[sessionUrl.path.length] != '/')
                        sessionUrl.path += '/'
                    sessionUrl.path += sessionKey
                    // END: old Url way
                    var transportClass = Orbited.util.chooseTransport()
                    cometTransport = new transportClass();
                    cometTransport.onReadFrame = transportOnReadFrame;
                    cometTransport.onclose = transportOnClose;
                    cometTransport.connect(sessionUrl.render())
                }
                
                else {
                    xhr = null;
                    self.readyState = self.READY_STATE_CLOSED;
                    self.onclose(Orbited.Errors.InvalidHandshake)
                }
            }
        }
        xhr.send(null);
    }
    
    /* 
     * self.send is only callable when readyState is OPEN. It will queue the data
     * up for delivery as soon as the upstream xhr is ready.
     */
    self.send = function(data) {
;;;     self.logger.debug('session.send', data)
        if (self.readyState != self.READY_STATE_OPEN) {
            throw new Error("Invalid readyState")
        }
        sendQueue.push([++packetCount, "data", data])
;;;     self.logger.debug('sending==', sending);
        if (!sending) {
;;;         self.logger.debug('starting send');
            doSend()
        }
    }

    /* 
     * self.close sends a close frame to the server, at the end of the queue.
     * It also sets the readyState to CLOSING so that no further data may be
     * sent. onclose is not called immediately -- it waits for the server to
     * send a close event.
     */
    self.close = function() {
        if (self.readyState != self.READY_STATE_OPEN) {
            throw new Error("Invalid readyState. Currently: " + self.readyState)
        }
        // TODO: don't have a third element (remove the null).
        sendQueue.push([++packetCount, "close", null])
        if (!sending) {
            doSend()
        }
        self.readyState = self.READY_STATE_CLOSING;
    }

    /* self.reset is a way to close immediately. The send queue will be discarded
     * and a close frame will be sent to the server. onclose is called immediately
     * without waiting for a reply from the server.
     */
    self.reset = function() {
        var origState = self.readyState
        self.readyState = self.READY_STATE_CLOSED;
        switch(origState) {
            case self.READY_STATE_INITIALIZED:
                self.onclose(Orbited.Errors.UserConnectionReset);
                break;
            case self.READY_STATE_OPENING:
                xhr.onreadystatechange = function() {};
                xhr.abort();
                self.onclose();
                break;
            case self.READY_STATE_OPEN:
                self.sendQueue = []
                self.sending = false;
                if (xhr.readyState < 4) {
                    xhr.onreadystatechange = function() {}
                    xhr.abort();
                }
                doClose(Orbited.Errors.UserConnectionReset);
                // TODO: send close frame
                //       -mcarter 7-29-08
                break;
            case self.READY_STATE_CLOSING:
                // TODO: Do nothing here?
                //       we need to figure out if we've attempted to send the close
                //       frame yet or not If not, we do something similar to case
                //       OPEN. either way, we should kill the transport and
                //       trigger onclose
                //       -mcarter 7-29-08                
                break;

            case self.READY_STATE_CLOSED:
                break
        }
    }

    var transportOnReadFrame = function(frame) {
;;;     self.logger.debug('READ FRAME');
;;;     self.logger.debug('id ', frame.id);
;;;     self.logger.debug('name ', frame.name);
;;;     if (frame.args.length > 0)
;;;         self.logger.debug('args ', frame.args[0]);
;;;     self.logger.debug('---');
        if (!isNaN(frame.id)) {
            lastPacketId = Math.max(lastPacketId, frame.id);
        }
;;;     self.logger.debug(frame)
        switch(frame.name) {
            case 'close':
                if (self.readyState < self.READY_STATE_CLOSED) {
                    doClose(Orbited.Statuses.ServerClosedConnection)
                }
                break;
            case 'data':
                self.onread(frame.args[0]);
                break;
            case 'open':
                if (self.readyState == self.READY_STATE_OPENING) {
                    self.readyState = self.READY_STATE_OPEN;
                    self.onopen();
                }
                else {
                    //TODO Throw and error?
                }
                break;
            case 'ping':
                // TODO: don't have a third element (remove the null).
                sendQueue.push([++packetCount, "ping", null])
                if (!sending) {
                    doSend()
                }
                
        }
    }
    var transportOnClose = function() {
;;;     self.logger.debug('transportOnClose');
        if (self.readyState < self.READY_STATE_CLOSED) {
            doClose(Orbited.Statuses.ServerClosedConnection)
        }
    }        
    var encodePackets = function(queue) {
        //TODO: optimize this.
        var output = []        
        for (var i =0; i < queue.length; ++i) {
            var frame = queue[i];
            for (var j =0; j < frame.length; ++j) {
                var arg = frame[j]
                if (arg == null) {
                    arg = ""
                }
                if (j == frame.length-1) {
                    output.push('0')
                }
                else {
                    output.push('1')
                }
                output.push(arg.toString().length)
                output.push(',')
                output.push(arg.toString())
            }
        }
        return output.join("")
    }

    var doSend = function(retries) {
;;;     self.logger.debug('in doSend');
        if (typeof(retries) == "undefined") {
            retries = 0
        }
        // TODO: I don't think this timeout formula is quite right...
        //       -mcarter 8-3-08
        if (retries*RETRY_INTERVAL >= RETRY_TIMEOUT) {
            doClose(Orbited.Errors.ConnectionTimeout)
            sending = false;
            return
        }
        if (sendQueue.length == 0) {
            sending = false;
            return
        }
        sending = true;
;;;     self.logger.debug('setting sending=true');
        var numSent = sendQueue.length
        sessionUrl.setQsParameter('ack', lastPacketId)
        xhr = createXHR();
        xhr.onreadystatechange = function() {
;;;         self.logger.debug('send readyState', xhr.readyState)
;;;         try {
;;;             self.logger.debug('status', xhr.status);
;;;         } catch(e) {
;;;             self.logger.debug('no status');
;;;         }
            switch(xhr.readyState) {
                
                case 4:
                    if (xhr.status == 200) {
                        sendQueue.splice(0, numSent)
                        return doSend();
                    }
                    else {
                        //TODO: implement retry back-off;
                        window.setTimeout(
                            function() {
                                doSend(++retries);
                            },
                            RETRY_INTERVAL
                        );
                    }
            }
        }
        var tdata = encodePackets(sendQueue)
;;;     self.logger.debug('post', retries, tdata);
        xhr.open('POST', sessionUrl.render(), true)
        xhr.send(tdata)

    }
    
    var doClose = function(code) {
;;;     self.logger.debug('doClose', code)
        self.readyState = self.READY_STATE_CLOSED;
        cometTransport.onReadFrame = function() {}
        if (cometTransport != null) {
            // TODO: is this line necessary?
            cometTransport.onclose = function() { }
            cometTransport.close()
        }
        self.onclose(code);

    }
};
Orbited.CometSession.prototype.logger = Orbited.getLogger("Orbited.CometSession");
Orbited.CometSession.prototype.READY_STATE_INITIALIZED  = 1;
Orbited.CometSession.prototype.READY_STATE_OPENING      = 2;
Orbited.CometSession.prototype.READY_STATE_OPEN         = 3;
Orbited.CometSession.prototype.READY_STATE_CLOSING      = 4;
Orbited.CometSession.prototype.READY_STATE_CLOSED       = 5;


Orbited.TCPSocket = function() {
    var self = this;

    // So we don't completely ambush people used to the 0.5 api...
    if (arguments.length > 0) {
        throw new Error("TCPSocket() accepts no arguments")
    }
    self.readyState = self.READY_STATE_INITIALIZED;
    self.onopen = function() { }
    self.onread = function() { }
    self.onclose = function() { }

    var session = null;
    var binary = false;
    var handshakeState = null;
    var hostname = null;
    var port = null;

    /* self.open attempts to establish a tcp connection to the specified remote
     * hostname on the specified port. When specified as true, the optional
     * argument, isBinary, will cause onread to return byte arrays, and send
     * will only accept a byte array.
     */
    self.open = function(_hostname, _port, isBinary) {
        if (self.readyState != self.READY_STATE_INITIALIZED) {
            // TODO: allow reuse from readyState == self.READY_STATE_CLOSED?
            //       Re-use makes sense for xhr due to memory concerns, but
            //       probably not for tcp sockets. How often do you reconnect
            //       in the same page?
            //       -mcarter 7-30-08
            throw new Error("Invalid readyState");
        }
        // handle isBinary undefined/null case
        binary = !!isBinary;
        self.readyState = self.READY_STATE_OPENING;
        hostname = _hostname;
        port = _port;
        session = new Orbited.CometSession()
        var sessionUrl = new Orbited.URL('/tcp')
        sessionUrl.domain = Orbited.settings.hostname
        sessionUrl.port = Orbited.settings.port
        sessionUrl.protocol = Orbited.settings.protocol
        session.open(sessionUrl.render())
        session.onopen = sessionOnOpen;
        session.onread = sessionOnRead;
        session.onclose = sessionOnClose;
        handshakeState = "initial";
    }

    self.close = function() {
        if (self.readyState != self.READY_STATE_OPEN && self.readyState != self.READY_STATE_OPENING) {
            throw new Error("Invalid readyState");
        }
        session.close();
    }
    
    /* self.reset closes the connection from this end immediately. The server
     * may be notified, but there is no guarantee. The main purpose of the reset
     * function is for a quick teardown in the case of a user navigation.
     * if reset is not called when IE navigates, for instance, there will be 
     * potential issues with future TCPSocket communication.
     */
    self.reset = function() {
        if (session)
            session.reset();
    }

    self.send = function(data) {
        if (!session) {
            throw new Error('how did this happen');
        }
        if (binary) {
            if (!(data instanceof Array)) {
                throw new Error("invalid payload: binary mode is set");
            }
            session.send(encodeBinary(data))
        }
        else {
;;;         self.logger.debug('SEND: ', data)
            session.send(data)
        }
       }

    var encodeBinary = Orbited.base64.encode;
    var decodeBinary = Orbited.base64.decode;

    var sessionOnRead = function(data) {
        switch(self.readyState) {
            case self.READY_STATE_OPEN:
;;;             self.logger.debug('READ: ', data)
                binary ? self.onread(decodeBinary(data)) : self.onread(data)
                break;
            case self.READY_STATE_OPENING:
                switch(handshakeState) {
                    case 'initial':
;;;                     self.logger.debug('initial');
;;;                     self.logger.debug('data', data)
;;;                     self.logger.debug('len', data.length);
;;;                     self.logger.debug('typeof(data)', typeof(data))
;;;                     self.logger.debug('data[0] ', data.slice(0,1))
;;;                     self.logger.debug('type ', typeof(data.slice(0,1)))
                        var result = (data.slice(0,1) == '1')
;;;                     self.logger.debug('result', result)
                        if (!result) {
;;;                         self.logger.debug('!result');
                            var errorCode = data.slice(1,4)
                            sessionOnClose = function() {}
                            session.close()
                            session = null;
                            self.onclose(parseInt(errorCode))
                        }
                        if (result) {
                            self.readyState = self.READY_STATE_OPEN;
;;;                         self.logger.debug('tcpsocket.onopen..')
                            self.onopen();
;;;                         self.logger.debug('did onopen');
                        }
                        break;
                }
                break;
        }
    }
    
    var sessionOnOpen = function(data) {
        // TODO: TCPSocket handshake
        session.send((binary ? '1' : '0') + hostname + ':' + port + '\n')
        handshakeState = 'initial'
    }
    
    var sessionOnClose = function(status) {
;;;     self.logger.debug('sessionOnClose');
        // If we are in the OPENING state, then the handshake code should
        // handle the close
        if (self.readyState >= self.READY_STATE_OPEN) {
            self.readyState = self.READY_STATE_CLOSED;
            session = null;
            self.onclose(status);
        }
    }
};
Orbited.TCPSocket.prototype.logger = Orbited.getLogger("Orbited.TCPSocket");
Orbited.TCPSocket.prototype.READY_STATE_INITIALIZED  = 1;
Orbited.TCPSocket.prototype.READY_STATE_OPENING      = 2;
Orbited.TCPSocket.prototype.READY_STATE_OPEN         = 3;
Orbited.TCPSocket.prototype.READY_STATE_CLOSING      = 4;
Orbited.TCPSocket.prototype.READY_STATE_CLOSED       = 5;





// XXX: the Orbited.XSDR stuff (presumably) doesn't work yet.
//      mcarter - 8-9-08 (~rev 476)

Orbited.singleton.XSDR = {
    receiveCbs: {},
    queues: {},
    id: 0,
    register: function(receive, queue) {
        var id = ++Orbited.singleton.XSDR;
        Orbited.singleton.XSDR.receiveCbs[id] = receive;
        Orbited.singleton.XSDR.queues[id] = queue;
    }
}

Orbited.XSDR = function() {
    var self = this;

    var ifr = null;
    var url;
    var method;
    var data;
    var requestHeaders;
    var queue = []
    var id = Orbited.singleton.XSDR.register(
        function(data) { receive(data) }, 
        queue
    )
    var bridgeUrl = new URL("")
    bridgeUrl.domain = Orbited.hostname
    bridgeUrl.port = Orbited.port
    bridgeUrl.path = '/static/xsdrBridge.html'
    bridgeUrl.hash = id;
    
    var reset = function() {
        self.responseText = ""
        self.status = null;
        self.readyState = 0;
        url = null;
        method = null;
        data = null;
        requestHeaders = {};

    }
    reset();

    self.open = function(_method, _url, async) {
        if (self.readyState == 4) {
            reset();
        }
        if (self.readyState != 0) {
            throw new Error("Invalid readyState");
        }
        if (!async) {
            throw new Error("Only Async XSDR supported")
        }
        self.readyState = 1;
        url = _url;
        method = _method;        
    }

    self.send = function(data) {
        if (self.readyState != 1) {
            throw new Error("Invalid readyState");
        }
        if (!ifr) {
            ifr = document.createElement("iframe")
            hideIframe(ifr);
            ifr.src = bridgeUrl.render()
            document.body.appendChild(ifr);
        }
        else {
            queue.push([method, url, data, requestHeaders]);
        }
    }

    self.abort = function() {
        if (self.readyState > 0 && self.readyState < 4) {
            queue.push(['ABORT']);
        }
    }

    self.setRequestHeader = function(key, val) {
        if (self.readyState != 0) {
            throw new Error("Invalid readyState");
        }
        requestHeaders[key] = val;
    }

    self.getResponseHeader = function() {
        if (self.readyState < 2) {
            throw new Error("Invalid readyState");
        }
        return responseHeaders[key]
    }

    var receive = function(payload) {
        switch(payload[0]) {
            case 'initialize':
                push([method, url, data, requestHeaders]);
                break;
            case 'readystatechange':
                var data = payload[1]
                self.readyState = data.readyState
                if (data.status) {
                    self.status = data.status
                }
                if (data.responseText) {
                    self.responseText += data.responseText
                }
                self.onreadystatechange();
        }
    }

    var hideIframe =function (ifr) {
        ifr.style.display = 'block';
        ifr.style.width = '0';
        ifr.style.height = '0';
        ifr.style.border = '0';
        ifr.style.margin = '0';
        ifr.style.padding = '0';
        ifr.style.overflow = 'hidden';
        ifr.style.visibility = 'hidden';
    }
    
}
Orbited.XSDR.prototype.logger = Orbited.getLogger("Orbited.XSDR");


/* Comet Transports!
 */

Orbited.CometTransports.XHRStream = function() {
    var self = this;
    var url = null;
    var xhr = null;
    var ackId = null;
    var offset = 0;
    var heartbeatTimer = null;
    var retryTimer = null;
    var buffer = ""
    var currentArgs = []
    var retryInterval = 50
    self.readyState = 0
    self.onReadFrame = function(frame) {}
    self.onread = function(packet) { self.onReadFrame(packet); }
    self.onclose = function() { }

    self.close = function() {
        if (self.readyState == 2) {
            return
        }
        if (xhr != null && (xhr.readyState > 1 || xhr.readyState < 4)) {
            xhr.onreadystatechange = function() { }
            xhr.abort()
            xhr = null;
        }
        self.readyState = 2
        window.clearTimeout(heartbeatTimer);
        window.clearTimeout(retryTimer);
        self.onclose();
    }

    self.connect = function(_url) {
        if (self.readyState == 1) {
            throw new Error("Already Connected")
        }
        url = new Orbited.URL(_url)
        if (xhr == null) {
            if (url.isSameDomain(location.href)) {
                xhr = createXHR();
            }
            else {
                xhr = new XSubdomainRequest(url.domain, url.port);
            }
        }
        url.path += '/xhrstream'
//        url.setQsParameter('transport', 'xhrstream')
        self.readyState = 1
        open()
    }
    var open = function() {
        try {
            if (typeof(ackId) == "number") {
                url.setQsParameter('ack', ackId)
            }
            if (typeof(xhr)== "undefined" || xhr == null) {
                throw new Error("how did this happen?");
            }
            
            xhr.open('GET', url.render(), true)
            xhr.onreadystatechange = function() {
                if (self.readyState == 2) { 
                    return
                }
;;;             self.logger.debug(xhr.readyState);
                switch(xhr.readyState) {
                    case 2:
                        // If we can't get the status, then we didn't actually
                        // get a valid xhr response -- we got a network error
                        try {
                            var status = xhr.status
                        }
                        catch(e) {
                            return
                        }
                        // If we got a 200, then we're in business
                        if (status == 200) {
                            heartbeatTimer = window.setTimeout(heartbeatTimeout, Orbited.settings.HEARTBEAT_TIMEOUT);
                            var testtimer = heartbeatTimer;
                        }
                        // Otherwise, case 4 should handle the reconnect,
                        // so do nothing here.
                        break;
                    case 3:
                        // If we can't get the status, then we didn't actually
                        // get a valid xhr response -- we got a network error
                        try {
                            var status = xhr.status
                        }
                        catch(e) {
                            return
                        }
                        // We successfully established a connection, so put the
                        // retryInterval back to a short value
                        if (status == 200) {
                            retryInterval = 50;
                            process();
                        }
                        break;
                    case 4:
                        try {
                            xhr.status
                        }
                        catch(e) {
                            // Expoential backoff: Every time we fail to 
                            // reconnect, double the interval.
                            // TODO cap the max value. 
                            retryInterval *= 2;
//                            self.logger.debug('retryInterval', retryInterval)
                            window.clearTimeout(heartbeatTimer);
                            window.setTimeout(reconnect, retryInterval)
                            return;
                        }

                        switch(xhr.status) {
                            case 200:
//                                alert('finished, call process');
//                               if (typeof(Orbited) == "undefined") {
//                                    alert('must have reloaded')
//                                    break
//                                }
//                                alert('a');
//                                alert('stream over ' +  typeof(console) + ' ' + typeof(Orbited) + ' ' + Orbited + ' ...');
                                process();
                                offset = 0;
                                setTimeout(open, 0)
                                window.clearTimeout(heartbeatTimer);
                                break;
                            case 404:
                                self.close();
                            default:
                                self.close();
                        }
                }
            }
            xhr.send(null);
        }
        catch(e) {
            self.close()
        }
    }

    var reconnect = function() {
//        self.logger.debug('reconnect...')
        if (xhr.readyState < 4 && xhr.readyState > 0) {
            xhr.onreadystatechange = function() {
                if (xhr.readyState == 4) {
                    reconnect();
                }
            }
//            self.logger.debug('do abort..')
            xhr.abort();
            window.clearTimeout(heartbeatTimer);            
        }
        else {
;;;         self.logger.debug('reconnect do open')
            offset = 0;
            setTimeout(open, 0)
        }
    }
    // 12,ab011,hello world
    var commaPos = -1;
    var argEnd = null;
    var frame = []
    var process = function() {
        var stream = xhr.responseText;
        receivedHeartbeat()

        // ignore leading whitespace, such as at the start of an xhr stream
        while (stream[offset] == ' ') {
            offset += 1
        }
        // ignore leading whitespace, such as at the start of an xhr stream
        while (stream[offset] == 'x') {
            offset += 1
        }

        var k = 0
        while (true) {
            k += 1
            if (k > 2000) {
                throw new Error("Borked XHRStream transport");
                return
            }
            if (commaPos == -1) {
                commaPos = stream.indexOf(',', offset)
            }
            if (commaPos == -1) {
                return
            }
            if (argEnd == null) {
                argSize = parseInt(stream.slice(offset+1, commaPos))
                argEnd = commaPos +1 + argSize
            }
            
            if (stream.length < argEnd) {
                return
            }
            var data = stream.slice(commaPos+1, argEnd)
            frame.push(data)
            var isLast = (stream.charAt(offset) == '0')
            offset = argEnd;
            argEnd = null;
            commaPos = -1
            if (isLast) {
                var frameCopy = frame
                frame = []
                receivedPacket(frameCopy)                
            }
        } 

    }
    var receivedHeartbeat = function() {
        window.clearTimeout(heartbeatTimer);
//        self.logger.debug('clearing heartbeatTimer', heartbeatTimer)
        heartbeatTimer = window.setTimeout(function() { 
//            self.logger.debug('timer', testtimer, 'did it'); 
            heartbeatTimeout();
        }, Orbited.settings.HEARTBEAT_TIMEOUT);
        var testtimer = heartbeatTimer;

//        self.logger.debug('heartbeatTimer is now', heartbeatTimer)
    }
    var heartbeatTimeout = function() {
//        self.logger.debug('heartbeat timeout... reconnect')
        reconnect();
    }
    var receivedPacket = function(args) {
        var testAckId = parseInt(args[0])
        if (!isNaN(testAckId)) {
            ackId = testAckId
        }
        var packet = {
            id: testAckId,
            name: args[1],
            args: args.slice(2)
        }
        self.onread(packet)
    }
}
Orbited.CometTransports.XHRStream.prototype.logger = Orbited.getLogger("Orbited.CometTransports.XHRStream");
// XHRStream supported browsers
Orbited.CometTransports.XHRStream.firefox = 1.0
Orbited.CometTransports.XHRStream.firefox2 = 1.0
Orbited.CometTransports.XHRStream.firefox3 = 1.0
Orbited.CometTransports.XHRStream.safari2 = 1.0
Orbited.CometTransports.XHRStream.safari3 = 1.0

Orbited.CometTransports.HTMLFile = function() {
    var self = this;
    var id = ++Orbited.singleton.HTMLFile.i;
    Orbited.singleton.HTMLFile.instances[id] = self;
    var htmlfile = null
    var ifr = null;
    var url = null;
    var restartUrl = null;
    var restartTimer = null;
    // TODO: move constant to Orbited.settings
    var baseRestartTimeout = 2000;
    var restartTimeout = baseRestartTimeout;
    self.onReadFrame = function(frame) {}
    self.onread = function(packet) { self.onReadFrame(packet); }
    self.onclose = function() { }
    self.connect = function(_url) {
        if (self.readyState == 1) {
            throw new Error("Already Connected")
        }
        url = new Orbited.URL(_url)
        url.path += '/htmlfile'
        url.setQsParameter('frameID', id.toString())
        self.readyState = 1
        doOpen(url.render())
    }

    var doOpenIfr = function() {
        
        var ifr = document.createElement('iframe')
        ifr.src = url.render()
        document.body.appendChild(ifr)
    }

    var doOpen = function(_url) {
        htmlfile = new ActiveXObject('htmlfile'); // magical microsoft object
        htmlfile.open();
//        htmlfile.write('<html><script>' + 'document.domain="' + document.domain + '";' + '</script></html>');
        htmlfile.write('<html></html>');
        htmlfile.parentWindow.Orbited = Orbited;
        htmlfile.close();
        var iframe_div = htmlfile.createElement('div');
        htmlfile.body.appendChild(iframe_div);
        ifr = htmlfile.createElement('iframe');
        iframe_div.appendChild(ifr);
        ifr.src = _url;
        restartUrl = _url;
        restartTimer = window.setTimeout(reconnect, restartTimeout)
    }
    
    // TODO: expose this in another way besides the public api
    self.restartingStream = function(_url) {
        restartUrl = _url;
        restartTimer = window.setTimeout(reconnect, restartTimeout)
    }
    
    var reconnect = function() {
;;;     self.logger.debug('doing reconnect... ' + restartTimeout);
        restartTimeout*=2;
        ifr.src = restartUrl;
        var restartTimer = window.setTimeout(reconnect, restartTimeout)        
    }

    self.streamStarted = function() {
;;;     self.logger.debug('stream started..');
        window.clearTimeout(restartTimer);
        restartTimer = null;
        restartTimeout = baseRestartTimeout;
    }
    
    self.streamClosed = function() {
;;;     self.logger.debug('stream closed!');
        window.clearTimeout(restartTimer);
        self.close()
    }

    self.receive = function(id, name, args) {
        packet = {
            id: id,
            name: name,
            args: args
        }
        self.onread(packet)
    }
    
    self.close = function() {
        if (self.readyState == 2) {
            return
        }
        self.readyState = 2
        ifr.src = 'about:blank'
        htmlfile = null;
        CollectGarbage();
        self.onclose();
    }

}
Orbited.CometTransports.HTMLFile.prototype.logger = Orbited.getLogger("Orbited.CometTransports.HTMLFile");
// HTMLFile supported browsers
Orbited.CometTransports.HTMLFile.ie = 1.0;
Orbited.singleton.HTMLFile = {
    i: 0,
    instances: {}
}




Orbited.CometTransports.SSE = function() {
    var self = this;

    self.onReadFrame = function(frame) {}
    self.onclose = function() { }
    self.readyState = 0;
    var heartbeatTimer = null;
    var source = null
    var url = null;
    var lastEventId = -1;

    self.close = function() {
        if (self.readyState == 2) {
            return;
        }
        // TODO: can someone test this and get back to me? (No opera at the moment)
        //     : -mcarter 7-26-08
        self.readyState = 2
        doClose();
        self.onclose();
    }

    self.connect = function(_url) {
        if (self.readyState == 1) {
            throw new Error("Already Connected")
        }
        url = new Orbited.URL(_url)
        url.path += '/sse'
        self.readyState = 1
        doOpen();
    }
    doClose = function() {
        source.removeEventSource(source.getAttribute('src'))
        source.setAttribute('src',"")
        if (opera.version() < 9.5) {
            document.body.removeChild(source)
        }
        source = null;
    }
    doOpen = function() {
/*
        if (typeof(lastEventId) == "number") {
            url.setQsParameter('ack', lastEventId)
        }
*/
        source = document.createElement("event-source");
        source.setAttribute('src', url.render());
        // NOTE: without this check opera 9.5 would make two connections.
        if (opera.version() < 9.5) {
            document.body.appendChild(source);
        }
        source.addEventListener('payload', receivePayload, false);

//        source.addEventListener('heartbeat', receiveHeartbeat, false);
        // start up the heartbeat timer...
//        receiveHeartbeat();
    }

    var receivePayload = function(event) {
        var data = eval(event.data);
        if (typeof(data) != 'undefined') {
            for (var i = 0; i < data.length; ++i) {
                var packet = data[i]
                receive(packet[0], packet[1], packet[2]);
            }
        }
    
    }
/*    var receiveHeartbeat = function() {
        window.clearTimeout(heartbeatTimer);
        heartbeatTimer = window.setTimeout(reconnect, Orbited.settings.HEARTBEAT_TIMEOUT)
    }
*/
    var receive = function(id, name, args) {
        var tempId = parseInt(id);
        if (!isNaN(tempId)) {
            // NOTE: The old application/x-dom-event-stream transport doesn't
            //       allow us to put in the lastEventId on reconnect, so we are
            //       bound to get double copies of some of the events. Therefore
            //       we are going to throw out the duplicates. Its not clear to
            //       me that this is a perfect solution.
            //       -mcarter 8-9-08
            if (tempId <= lastEventId) {
                return
            }
            lastEventId = tempId;
        }
        // NOTE: we are dispatching null-id packets. Is this correct?
        //       -mcarter 9-8-08
        packet = {
            id: id,
            name: name,
            args: args
        }
        self.onReadFrame(packet)
    }
}
Orbited.CometTransports.SSE.prototype.logger = Orbited.getLogger("Orbited.CometTransports.SSE");

Orbited.CometTransports.SSE.opera = 1.0;
Orbited.CometTransports.SSE.opera8 = 1.0;
Orbited.CometTransports.SSE.opera9 = 1.0;
Orbited.CometTransports.SSE.opera9_5 = 0.8;



/* This is an old implementation of the URL class. Jacob is cleaning it up
 * mcarter, 7-30-08
 */
Orbited.URL = function(_url) {
    var self = this;
    var protocolIndex = _url.indexOf("://")
    if (protocolIndex != -1)
        self.protocol = _url.slice(0,protocolIndex)
    else
        protocolIndex = -3
    var domainIndex = _url.indexOf('/', protocolIndex+3)
    if (domainIndex == -1)
        domainIndex=_url.length
    var hashIndex = _url.indexOf("#", domainIndex)
    if (hashIndex != -1)
        self.hash = _url.slice(hashIndex+1)
    else
        hashIndex = _url.length
    var uri = _url.slice(domainIndex, hashIndex)
    var qsIndex = uri.indexOf('?')
    if (qsIndex == -1)
        qsIndex=uri.length
    self.path = uri.slice(0, qsIndex)
    self.qs = uri.slice(qsIndex+1)
    if (self.path == "")
        self.path = "/"
    var domain = _url.slice(protocolIndex+3, domainIndex)
    var portIndex = domain.indexOf(":")
    if (portIndex == -1) {
        self.port = 80
        portIndex = domain.length
    }
    else {
        self.port = parseInt(domain.slice(portIndex+1))
    }
    if (isNaN(this.port))
        throw new Error("Invalid _url")
    self.domain = domain.slice(0, portIndex)

    self.render = function() {
        var output = ""
        if (typeof(self.protocol) != "undefined")
            output += self.protocol + "://"
        output += self.domain
        if (self.port != 80 && typeof(self.port) != "undefined" && self.port != null)
            if (typeof(self.port) != "string" || self.port.length > 0)
                output += ":" + self.port
        if (typeof(self.path) == "undefined" || self.path == null)
            output += '/'
        else
            output += self.path
        if (self.qs.length > 0)
            output += '?' + self.qs
        if (typeof(self.hash) != "undefined" && self.hash.length > 0)
            output += "#" + self.hash
        return output
    }
    self.isSameDomain = function(_url) {
        _url = new Orbited.URL(_url)

        if (!_url.domain || !self.domain)
            return true
        return (_url.port == self.port && _url.domain == self.domain)
    }
    self.isSameParentDomain = function(_url) {
        _url = new Orbited.URL(_url)
        if (_url.domain == self.domain) {
            return true;
        }
        var orig_domain = _url.domain;
        var parts = document.domain.split('.')
//        var orig_domain = document.domain
        for (var i = 0; i < parts.length-1; ++i) {
            var new_domain = parts.slice(i).join(".")
            if (orig_domain == new_domain)
                return true;
        }
        return false
    }

    var decodeQs = function(qs) {
    //    alert('a')
        if (qs.indexOf('=') == -1) return {}
        var result = {}
        var chunks = qs.split('&')
        for (var i = 0; i < chunks.length; ++i) {
            var cur = chunks[i]
            var pieces = cur.split('=')
            result[pieces[0]] = pieces[1]
        }
        return result
    }
    var encodeQs = function(o) {
            var output = ""
            for (var key in o)
                output += "&" + key + "=" + o[key]
            return output.slice(1)
        }
    self.setQsParameter = function(key, val) {
        var curQsObj = decodeQs(self.qs)
        curQsObj[key] = val
        self.qs = encodeQs(curQsObj)
    }

    self.mergeQs = function(qs) {
        var newQsObj = decodeQs(qs)
        for (key in newQsObj) {
            curQsObj[key] = newQsObj[key]
        }
    }
    self.removeQsParameter = function(key) {
        var curQsObj = decodeQs(self.qs)
        delete curQsObj[key]
        self.qs = encodeQs(curQsObj)
    }

    self.merge = function(targetUrl) {
        if (typeof(self.protocol) != "undefined" && self.protocol.length > 0) {
            self.protocol = targetUrl.protocol
        }
        if (targetUrl.domain.length > 0) {
            self.domain = targetUrl.domain
            self.port = targetUrl.port
        }
        self.path = targetUrl.path
        self.qs = targetUrl.qs
        self.hash = targetUrl.hash
    }

}



})();
