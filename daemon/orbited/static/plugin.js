function send_xhr(url, args) {
        var qs = "?";
        var xhr = Orbited.create_xhr();
        for (key in args) {
            var val = args[key];
            qs = qs + "&" + key + "=" + val;
        }
        xhr.open("GET", url + qs, true);
        xhr.send(null);
        return xhr;
}

function get(url,args) {

	var xhr = this.send_xhr(url, {});
	var cb = {
		success: function(uname) { },
		failure: function(err) {
			console.log(err);
		}
	}
	xhr.onreadystatechange = function() {
		if (xhr.readyState == 4) {
			if (xhr.status == 200) {
				var result = eval(xhr.responseText);
				cb.success(result);
			}
			else {
				cb.failure(xhr.statusText);
			}
		}
	}
	return cb;
}

function get_user_key(cb) {
	get(base_url+'/connect',{}).success = cb;
}

function start_app() {
    base_url = String(document.location);
    get_user_key(start_app_callback);
}

function start_app_callback(session_key) {
    session_key = session_key;
    Orbited.connect(receive_event, 'user', base_url+'/event', session_key);
}

start_app();
