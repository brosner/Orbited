Revolved = {
    channel_callbacks: {},

    connect: function(server, port, resource) {
        this.publish_queue = []
        this.publishing = false;
        this.server = server;
        this.port = port;
        this.resource = resource;
        if (this.resource == null) 
            this.resource = "default"
        this.userId = null;
        this.userToken = null;
        this.base_url = "http://" + server + ":" + port + "/_/revolved/";
        url = this.base_url + "event";
        var qs = '';
        if(this.resource) { qs = '?resource='+this.resource; }
        xhr = this.send_xhr("connect", {}, qs);
        cb = {
            success: function(uname) { },
            failure: function(err) {
//                console.log(err);
//                console.log("retrying Revolved.connect");
                Revolved.connect(server, port, resource);
            }
        }
        xhr.onreadystatechange = function() {
            if (xhr.readyState == 4) {
                if (xhr.status == 200) {
                    res = eval(xhr.responseText)
                    if (res.length > 0 && res[0] == "success") {
                        Revolved.sessionKey = res[1];
                        Revolved.userId = res[2];
                        Orbited.connect(Revolved.event, Revolved.userId, url, Revolved.sessionKey);
                        cb.success(res[2]);
                    }
                    else {
                        cb.failure(res[1]);
                    }
                } 
                else {
                    cb.failure(xhr.statusText);
                }
            }
        }
        return cb;
    },

    event: function(data) {
//        console.log(data);
        var type = data[0]
        switch(type) {
            case 'publish':
                var channel = data[1]
                var sender = data[2]
                var message = eval(data[3])
                Revolved.channel_callbacks[channel](channel, sender, message)
                break;
            case 'system':
                break;
        }
    },
    publish_success: function() {
//        console.log("publish success!");
        this.publishing = false;
        this.publish_next();
    },
    publish_next: function() {
        var self = this;
        if (this.publishing) { 
            //console.log("already publishing...");
            return 
        }
        req = this.publish_queue.shift()
        if (req != null) {
            this.publishing = true;
//            console.log(["publish", req])
            channel = req[0]
            payload = req[1]
            xhr = this.send_xhr('publish', { channel: channel, payload: escape(JSON.stringify(payload)) })
            xhr.onreadystatechange = function() {
                try {
//                    console.log("change state: ")
//                    console.log(xhr.readyState)
//                    console.log(xhr.status);
                    if (xhr.readyState == 4) {
                        if (xhr.status == 200) {
                            self.publish_success();
                        } 
                    }
                }
                catch(e) {
                }
            }
        }
    },
    publish2: function(channel, payload) {
//        ("publishing! " + channel + payload);
        if (this.userId) {
            this.publish_queue.push([channel, payload])
            this.publish_next()
        }
        else {
//            console.log('lurkers cannot publish');
        }
    },
    publish: function(channel, payload) {
        if (this.userId) {
            xhr = this.send_xhr('publish', { channel: channel, payload: escape(JSON.stringify(payload)) })

        }
        else {
//            console.log('lurkers cannot publish');
        }

    },
    make_qs: function(userId, userToken) {
        var qs = "?session=" + this.sessionKey;
        if (userId) {
            qs += "&userid=" + userId;
        }
        if (userToken) {
            qs += "&token=" + userToken;
        }
        return qs;
    },

    authenticate: function(userId, userToken) {
        if (! this.sessionKey) {
            //console.log("must call connect before authenticate");
            return false;
        }
        /*if (! userId) {
            console.log("must provide user name");
            return false;
        }*/
        var qs = this.make_qs(userId,userToken);
        xhr = this.send_xhr("authenticate", {}, qs)
        cb = {
            success: function() { },
            failure: function(err) { }//console.log(err); }
        }
        xhr.onreadystatechange = function() {
            if (xhr.readyState == 4) {
                if (xhr.status == 200) {
                    var res = eval(xhr.responseText);
                    if (res == "success") {
                        Revolved.userId = userId;
                        Revolved.userToken = userToken;
                        cb.success();
                    }
                    else {
                        cb.failure(res[1]);
                    }
                }
                else {
                    cb.failure(xhr.statusText);
                }
            }
        }
        return cb;
    },

    subscribe: function(channel, callback) {
        if (this.channel_callbacks[channel] != null) {
            this.channel_callbacks[channel] = callback
            return;
        }
        this.channel_callbacks[channel] = callback
        this.send_xhr('subscribe', { channel: channel })
    },

    unsubscribe: function(channel) {
        if (this.channel_callbacks[channel] == null) {
            return;
        }
        delete this.channel_callbacks[channel]
        this.send_xhr('unsubscribe', { channel: channel })
    },

    send_xhr: function(location, args, qs) {
        if (qs == null) {
            qs = "?session=" + this.sessionKey
        }
        xhr = this.create_xhr()
        for (key in args) {
            val = args[key]
            qs = qs + "&" + key + "=" + val
        }
        xhr.open("GET", this.base_url + location + qs, true);
        xhr.send(null);
        return xhr
    },

  create_xhr: function() {
    try { return new ActiveXObject("Msxml2.XMLHTTP"); } catch (e) {}
    try { return new ActiveXObject("Microsoft.XMLHTTP"); } catch (e) {}
    try { return new XMLHttpRequest(); } catch(e) {}
    return null;
  }
}


/*jslint evil: true */
/*extern JSON */

if (!this.JSON) {

    JSON = function () {

        function f(n) {    // Format integers to have at least two digits.
            return n < 10 ? '0' + n : n;
        }

        Date.prototype.toJSON = function () {

// Eventually, this method will be based on the date.toISOString method.

            return this.getUTCFullYear()   + '-' +
                 f(this.getUTCMonth() + 1) + '-' +
                 f(this.getUTCDate())      + 'T' +
                 f(this.getUTCHours())     + ':' +
                 f(this.getUTCMinutes())   + ':' +
                 f(this.getUTCSeconds())   + 'Z';
        };


        var m = {    // table of character substitutions
            '\b': '\\b',
            '\t': '\\t',
            '\n': '\\n',
            '\f': '\\f',
            '\r': '\\r',
            '"' : '\\"',
            '\\': '\\\\'
        };

        function stringify(value, whitelist) {
            var a,          // The array holding the partial texts.
                i,          // The loop counter.
                k,          // The member key.
                l,          // Length.
                r = /["\\\x00-\x1f\x7f-\x9f]/g,
                v;          // The member value.

            switch (typeof value) {
            case 'string':

// If the string contains no control characters, no quote characters, and no
// backslash characters, then we can safely slap some quotes around it.
// Otherwise we must also replace the offending characters with safe sequences.

                return r.test(value) ?
                    '"' + value.replace(r, function (a) {
                        var c = m[a];
                        if (c) {
                            return c;
                        }
                        c = a.charCodeAt();
                        return '\\u00' + Math.floor(c / 16).toString(16) +
                                                   (c % 16).toString(16);
                    }) + '"' :
                    '"' + value + '"';

            case 'number':

// JSON numbers must be finite. Encode non-finite numbers as null.

                return isFinite(value) ? String(value) : 'null';

            case 'boolean':
            case 'null':
                return String(value);

            case 'object':

// Due to a specification blunder in ECMAScript,
// typeof null is 'object', so watch out for that case.

                if (!value) {
                    return 'null';
                }

// If the object has a toJSON method, call it, and stringify the result.

                if (typeof value.toJSON === 'function') {
                    return stringify(value.toJSON());
                }
                a = [];
                if (typeof value.length === 'number' &&
                        !(value.propertyIsEnumerable('length'))) {

// The object is an array. Stringify every element. Use null as a placeholder
// for non-JSON values.

                    l = value.length;
                    for (i = 0; i < l; i += 1) {
                        a.push(stringify(value[i], whitelist) || 'null');
                    }

// Join all of the elements together and wrap them in brackets.

                    return '[' + a.join(',') + ']';
                }
                if (whitelist) {

// If a whitelist (array of keys) is provided, use it to select the components
// of the object.

                    l = whitelist.length;
                    for (i = 0; i < l; i += 1) {
                        k = whitelist[i];
                        if (typeof k === 'string') {
                            v = stringify(value[k], whitelist);
                            if (v) {
                                a.push(stringify(k) + ':' + v);
                            }
                        }
                    }
                } else {

// Otherwise, iterate through all of the keys in the object.

                    for (k in value) {
                        if (typeof k === 'string') {
                            v = stringify(value[k], whitelist);
                            if (v) {
                                a.push(stringify(k) + ':' + v);
                            }
                        }
                    }
                }

// Join all of the member texts together and wrap them in braces.

                return '{' + a.join(',') + '}';
            }
        }

        return {
            stringify: stringify,
            parse: function (text, filter) {
                var j;

                function walk(k, v) {
                    var i, n;
                    if (v && typeof v === 'object') {
                        for (i in v) {
                            if (Object.prototype.hasOwnProperty.apply(v, [i])) {
                                n = walk(i, v[i]);
                                if (n !== undefined) {
                                    v[i] = n;
                                }
                            }
                        }
                    }
                    return filter(k, v);
                }


// Parsing happens in three stages. In the first stage, we run the text against
// regular expressions that look for non-JSON patterns. We are especially
// concerned with '()' and 'new' because they can cause invocation, and '='
// because it can cause mutation. But just to be safe, we want to reject all
// unexpected forms.

// We split the first stage into 4 regexp operations in order to work around
// crippling inefficiencies in IE's and Safari's regexp engines. First we
// replace all backslash pairs with '@' (a non-JSON character). Second, we
// replace all simple value tokens with ']' characters. Third, we delete all
// open brackets that follow a colon or comma or that begin the text. Finally,
// we look to see that the remaining characters are only whitespace or ']' or
// ',' or ':' or '{' or '}'. If that is so, then the text is safe for eval.

                if (/^[\],:{}\s]*$/.test(text.replace(/\\./g, '@').
replace(/"[^"\\\n\r]*"|true|false|null|-?\d+(?:\.\d*)?(:?[eE][+\-]?\d+)?/g, ']').
replace(/(?:^|:|,)(?:\s*\[)+/g, ''))) {

// In the second stage we use the eval function to compile the text into a
// JavaScript structure. The '{' operator is subject to a syntactic ambiguity
// in JavaScript: it can begin a block or an object literal. We wrap the text
// in parens to eliminate the ambiguity.

                    j = eval('(' + text + ')');

// In the optional third stage, we recursively walk the new structure, passing
// each name/value pair to a filter function for possible transformation.

                    return typeof filter === 'function' ? walk('', j) : j;
                }

// If the text is not JSON parseable, then a SyntaxError is thrown.

                throw new SyntaxError('parseJSON');
            }
        };
    }();
}


/*
try {
    Revolved.initialize(user_name, app_name, token)
    Revolved.connect(master_server)
}
catch (Exception e) {
    SAF
}

{
    'channel': ('string', '

class StockEvent(Payload):
    String  channel
    Integer id
    String  symbol
    Integer value

class Subscription:
    rules:
        topic == "stock"
        symbol == "NYSE"
        price > 40


Revolved.publish(payload)

Revolved.subscribe(channel, callback)
Revolved.publish(channel, payload)
Revolved.send(user, payload, app_name)

Resolved.publish({ 
    'channel': ('string', 'orbited_livehelp'),
    'type': ('string', 'message'),
    'content': ('string', 'hello')
    })

event(payloads):
    for payload in payloads:
        if payload.channel == "stock":


*/