// we set the ie_nocache variable to avoid caching issues in IE

var ie_nocache = 0;
var event_iframe = document.getElementById('events');

// This is just boilerplate to create an XHR object. Should work on most
// browsers.

create_xhr = function() {
  try { return new ActiveXObject("Msxml2.XMLHTTP"); } catch (e) {}
  try { return new ActiveXObject("Microsoft.XMLHTTP"); } catch (e) {}
  try { return new XMLHttpRequest(); } catch(e) {}
  return null;
}

// We need to do two things to connect. 1) Initialize the Orbited event
// stream. In this case we are using the iframe transport. 2) We need to
// let the chat server know we are connected so it sends us any future
// messages.

connect = function() {
  name = document.getElementById('nickname').value;
  event_iframe.src='/cherrychat?user=' + name + '&session=0&transport=iframe';
  join(name);
}

join = function(user) {
  xhr = create_xhr();
  xhr.open("GET", "/join?user=" + user, true);
  xhr.send(null);
}

send_msg = function() {
  ie_nocache += 1;
  xhr = create_xhr();
  msg = document.getElementById('chat').value;
  nickname = document.getElementById('nickname').value;
  xhr.open("GET", "/msg?id=" + ie_nocache + "&user=" + name + "&msg=" + msg, true);
  xhr.send(null);
}

// This is the function that Orbited will call from the iframe whenever it
// receives an event. We are expecting data to be a string and we just want
// to dump the whole string into the chat_box.  The iframe transport always
// calls a function called 'e' inside the iframe, with events.

event_iframe.e = function(data) {
  chat_box = document.getElementById('box');
  div = window.parent.document.createElement('div');
  div.className = "event";
  div.innerHTML = data;
  chat_box.appendChild(div);
  chat_box.scrollTop = chat_box.scrollHeight;
}