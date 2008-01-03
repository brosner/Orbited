/*
Orbited.connect(got_event) // Tries to find the best option
Orbited.connect(got_event, "htmlfile") // Useses ie htmlfile
Orbited.connect(got_event, "longpoll") // No such transport at the moment
*/

Orbited = {

  connect: function (event_cb, user, location, session, transport) {
    this.user = user;
    this.location = location;
    this.transport = transport;
    this.session = session;
    if (typeof transport === 'undefined') {
      transport = this.find_best_transport();
    }
    // the transport for 'htmlfile' from the server side is just 'iframe'
    var connection_transport = (transport === 'htmlfile') ? 'iframe' : transport
    this.url = location + '?user=' + user + '&session=' + session +
               '&transport=' + connection_transport;
    this.event_cb = event_cb;
    document.domain = this.extract_xss_domain(document.domain);

    this['connect_' + transport]();
  },

  find_best_transport: function () {
    // IF we're on IE 5.01/5.5/6/7 we want to use an htmlfile
    try {
      var test = ActiveXObject;
      return 'htmlfile';
    }
    catch (e) {}

    // If the browser supports server-sent events, we should use those
    if ((typeof window.addEventStream) === 'function') {
      return 'server_sent_events';
    }

    // // Otherwise use the iframe transport
    // return 'iframe';

    // otherwise use xhr streaming
    return 'xhr_stream';
  },

  connect_iframe: function () {
    var ifr = document.createElement('iframe');
    this.hide_iframe(ifr);
    ifr.setAttribute('id', 'orbited_event_source');
    ifr.setAttribute('src', this.url);
    document.body.appendChild(ifr);
    this.kill_load_bar();
    var self = this;
    var event_cb = this.event_cb;
    this.event_cb = function (data) {
      event_cb(data);
      self.kill_load_bar();
    }
  },

  connect_htmlfile: function() {  
    var htmlfile = new ActiveXObject('htmlfile'); // magical microsoft object
    htmlfile.open();
    htmlfile.write('<html><script>' +
                   'document.domain="' + document.domain + '";' +
                   '</script></html>');
    htmlfile.parentWindow.Orbited = this;
    htmlfile.close();
    var iframe_div = htmlfile.createElement('div');
    htmlfile.body.appendChild(iframe_div);
    iframe_div.innerHTML = '<iframe src="' + this.url + '"></iframe>';
    this.htmlfile = htmlfile;
    var self = this;
    function close_htmlfile () {
      htmlfile = null;
      self.htmlfile = null;
      CollectGarbage();
    }
    document.attachEvent('on'+'unload', close_htmlfile)
  },

  connect_xhr_stream: function () {
    var boundary = '\r\n|O|\r\n';
    var event_cb = this.event_cb;
    var xhr;
    var offset;
    var length_seen;
    var response_stream;
    var self = this;

    function connect() {
      offset = 0;
      length_seen = 0;
      xhr = self.create_xhr();
      xhr.onreadystatechange = function () {
        try {
          if (xhr.status != 200) {
            Orbited.log('xhr failed (status not 200)');
            return false;
          }
        }
        catch(e) {
          return false;
        }
        // We have some new data
        if (xhr.readyState == 3) {
          handle_event();
        }
        // Connection is finished.
        if (xhr.readyState == 4) {
          handle_event();
        }
      };
      xhr.open('GET', self.url, true);
      xhr.send(null);

      // After 30 seconds, abort the connection, and re-connect
      // TODO: this should really be done server-side, after some specified
      // amount of data; doing it here could result in missed events.
      setTimeout(function () {
        xhr.abort();
        xhr = null;
        connect();
      }, 30000);
    }

    function handle_event() {
      response_stream = xhr.responseText;

      // If there's no new text, bail out.
      if (response_stream.length === offset ||
          response_stream.length === length_seen) {
        return;
      }

      // At the very start of the file, skip initial padding (needed for
      // safari), or if we haven't gotten through it yet, bail out--reset
      // offset so this gets tried again later
      if (offset === 0) {
        offset = response_stream.indexOf('\r\n\r\n');
        if (offset === -1) {
          offset = 0;
          length_seen = response_stream.length;
          return;
        }
      };

      // find the next boundary, starting at our offset
      var next_boundary = response_stream.indexOf(boundary, offset);

      // if we can't find any end boundaries, bail out
      if (next_boundary === -1) {
        length_seen = response_stream.length;
        return;
      }

      // we maybe got a ping if we have 2 boundaries in a row
      if (offset == next_boundary) {
        handle_ping();
      } else {
        // between offset and next_boundary lies our payload.
        var data = response_stream.slice(offset, next_boundary);
        offset = next_boundary + boundary.length;
        handle_data(data);        
      }

      // try again; we may have gotten multiple events at once
      handle_event();
    }

    function handle_ping() {
      // if response_stream starts with ping + boundary, we got a ping.
      // to handle it just increment the offset
      if (response_stream.indexOf('ping' + boundary, offset) === offset) {
        offset += ('ping' + boundary).length;
      }
    }

    function handle_data(data) {
      data = eval(data);
      if (typeof data !== 'undefined') {
        event_cb(data);
      }
    }

    connect();
  },

  connect_xhr_multipart: function () {
    var xhr = this.create_xhr();
    var event_cb = this.event_cb;
    xhr.onreadystatechange = function () {
      try {
        if (xhr.status != 200) {
          Orbited.log('XHR status not 200');
          return;
        }
      }
      catch(e) {
        return;
      }
      // We have a new event
      if (xhr.readyState == 4) {
        var data = eval(xhr.responseText);
        if (typeof data !== 'undefined') {
          event_cb(data);          
        }
      }
    };
    xhr.multipart = true;
    xhr.open('GET', this.url, true);
    xhr.send(null);
  },

  connect_server_sent_events: function () {
    var es = document.createElement('event-source');
    es.setAttribute('src', this.url);
    document.body.appendChild(es);

    var event_cb = this.event_cb;
    es.addEventListener('orbited', function (event) {
      var data = eval(event.data);
      if (typeof data !== 'undefined') {
        event_cb(data);
      }
    }, false);
  },

  extract_xss_domain: function (old_domain) {
    domain_pieces = old_domain.split('.');
    if (domain_pieces.length === 4) {
      var is_ip = !isNaN(Number(domain_pieces.join('')));
      if (is_ip) {
        return old_domain;
      }
    }
    return domain_pieces.slice(-2).join('.');
  },

  attach_iframe: function(ifr) {
      ifr.e = this.event_cb;
  },

  hide_iframe: function (ifr) {
    ifr.style.display = 'block';
    ifr.style.width = '0';
    ifr.style.height = '0';
    ifr.style.border = '0';
    ifr.style.margin = '0';
    ifr.style.padding = '0';
    ifr.style.overflow = 'hidden';
    ifr.style.visibility = 'hidden';
  },

  create_xhr: function () {
    try { return new ActiveXObject('MSXML3.XMLHTTP'); } catch(e) {}
    try { return new ActiveXObject('MSXML2.XMLHTTP.3.0'); } catch(e) {}
    try { return new ActiveXObject('Msxml2.XMLHTTP'); } catch(e) {}
    try { return new ActiveXObject('Microsoft.XMLHTTP'); } catch(e) {}
    try { return new XMLHttpRequest(); } catch(e) {}
    throw new Error('Could not find XMLHttpRequest or an alternative.');
  },

  log: function (arg) {
    if (typeof window.console !== 'undefined') {
      console.log(arg);
    }
    else if (typeof window.opera !== 'undefined') {
      opera.postError(arg);
    }
  },

  kill_load_bar: function () {
    if (typeof this.load_kill_ifr === 'undefined') {
      this.load_kill_ifr = document.createElement('iframe');
      this.hide_iframe(this.load_kill_ifr);
    }
    document.body.appendChild(this.load_kill_ifr);
    document.body.removeChild(this.load_kill_ifr);
  }
};
