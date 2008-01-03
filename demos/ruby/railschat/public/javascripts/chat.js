// we set the ie_nocache variable to avoid caching issues in IE

var ie_nocache = 0;

// We need to do two things to connect. 1) Initialize the Orbited event
// stream. Using the Orbited object of orbited.js, we can use a uniform API
// to connect to events, with no need for complex custom javascript to handle
// various transports. 2) We need to let the chat server know we are connected
// so it sends us any future messages.

connect = function() {
  var name = document.getElementById('nickname').value;
  Orbited.connect(chat_event, name, "/railschat", "0");
  join(name);
}

// Here we actually create the request to the chat server to join the chat.
// This is just a helper function that is called by connect.  Notice we can
// use the create_xhr function of the Orbited object to easily obtain an
// XHR object on any browser supporting XHR.

join = function(user) {
  var xhr = Orbited.create_xhr();
  xhr.open("GET", "/chat/join?user=" + user, true);
  xhr.send(null);
}

// This will get the contents out of msg input box and send it to the server.

send_msg = function() {
  ie_nocache += 1;
  var xhr = Orbited.create_xhr();
  var msg = document.getElementById('chat').value;
  var name = document.getElementById('nickname').value;
  xhr.open("GET", "/chat/msg?id=" + ie_nocache + "&user=" + name + "&msg=" + msg, true);
  xhr.send(null);
}

// We supplied chat_event as a callback to the Orbited.connect function,
// so this will be called for each new event we receive.  In this case,
// our callback just adds the payload of each event to a new div in the
// chat history box.
   
chat_event = function(data) {
  var chat_box = document.getElementById('box');
  var div = window.parent.document.createElement('div');
  div.className = "event";
  div.innerHTML = data;
  chat_box.appendChild(div);
  chat_box.scrollTop = chat_box.scrollHeight;
}