/* 
 * This is just boilerplate to create an XHR object. Should work on most
 * browsers.
 */
id = 0
var old_xhr;
var name;
function createXMLHttpRequest() {
  try { return new ActiveXObject("Msxml2.XMLHTTP"); } catch (e) {}
  try { return new ActiveXObject("Microsoft.XMLHTTP"); } catch (e) {}
  try { return new XMLHttpRequest(); } catch(e) {}
  return null;
}

function long_polling() {
  xhr = createXMLHttpRequest()
  xhr.onreadystatechange = function() {
    orbited_event(xhr);
  }
  xhr.open("GET", "/cherrychat|" + name + ',0,xhr', true);
  xhr.send(null);
}

function orbited_event(xhr) {
  try {
    if (xhr.status  == 200) { 
      if (xhr.readyState == 4) {
        old_xhr = xhr;
        data = eval(xhr.responseText)
        if (data != undefined) {
          event(data);
        }
        long_polling();
      }
    }
    else {
      alert("failed");
    }
  }
  catch(e) {}
}

/* 
 * We need to do two things to connect. 1) Initialize the orbited event
 * stream. In this case we are using the iframe transport. 2) We need to
 * let the chat server know we are connected so it sends us any future
 * messages.
 */
function connect() {
  name = document.getElementById('nickname').value;
  e = document.getElementById('events');
  long_polling();
//  e.src='/cherrychat|' + name + ',0,iframe'
  join(name);
}

/* 
 * Here we actually create the request to the chat server to join the chat.
 * This is just a helper function that is called by connect.
 */
function join(user) {
  xmlhttp = createXMLHttpRequest();
  xmlhttp.open("GET", "/join?user=" + user, true);
  xmlhttp.send(null);
}

/* 
 * This will get the contents out of msg input box and send it to the server.
 */
function send_msg() {
  id = id + 1
  xmlhttp = createXMLHttpRequest();
  msg = document.getElementById('chat').value;
  nickname = document.getElementById('nickname').value;
  xmlhttp.open("GET", "/msg?id=" + id + "&user=" + nickname + "&msg=" + msg, true);
  xmlhttp.send(null);
}

/* 
 * This is the function that orbited will call from the iframe whenever it
 * receives an event. We are expecting data to be a string and we just want
 * to dump the whole string into the chat_box.
 */
function event(data) {
  chat_box = document.getElementById('box');
  div = window.parent.document.createElement('div');
  div.className = "event";
  div.innerHTML = data;
  chat_box.appendChild(div);
  chat_box.scrollTop = chat_box.scrollHeight;
}