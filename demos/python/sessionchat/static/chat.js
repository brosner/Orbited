var ie_nocache= 1

/* 
 * We need to do two things to connect. 1) Initialize the orbited event
 * stream. In this case we are using the iframe transport. 2) We need to
 * let the chat server know we are connected so it sends us any future
 * messages.
 */

connect = function() {
  var name = document.getElementById('nickname').value;
  Orbited.connect(chat_event, name, "/cherrychat", "0");
  join(name);
}

/* 
 * Here we actually create the request to the chat server to join the chat.
 * This is just a helper function that is called by connect.
 */

function join(user) {
  var xhr = Orbited.create_xhr();
  xhr.open("GET", "/join?user=" + user, true);
  xhr.send(null);
}

/* 
 * This will get the contents out of msg input box and send it to the server.
 */

function send_msg() {
  ie_nocache += 1;
  var xhr = Orbited.create_xhr();
  var msg = document.getElementById('chat').value;
  var name = document.getElementById('nickname').value;
  xhr.open("GET", "/msg?id=" + ie_nocache + "&user=" + name + "&msg=" + msg, true);
  xhr.send(null);
}

/* 
 * This is the function that orbited will call from the iframe whenever it
 * receives an event. We are expecting data to be a string and we just want
 * to dump the whole string into the chat_box.
 */
   
function chat_event(data) {
  var chat_box = document.getElementById('box');
  var div = window.parent.document.createElement('div');
  div.className = "event";
  div.innerHTML = data;
  chat_box.appendChild(div);
  chat_box.scrollTop = chat_box.scrollHeight;
}