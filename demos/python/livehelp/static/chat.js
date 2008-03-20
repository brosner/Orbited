// set the following in a "config" script to change settings
/*TOP_DOMAIN = null;
CHANNEL = '#orbited_test';
ORBIT_HOSTNAME = null;
APP_HOSTNAME = null;
*/
orig_domain = document.domain;
nickname = null;
loggedOn = false;
users = {}

function request(url, params) {
  $.get(url, params); // ajax get request
}

function connect() {
  if (loggedOn) {
    alert("You’re already logged in.");
  }
  else {
    nickname = $("#nickname").val();
    Orbited.log([chat_event, nickname, ORBIT_HOSTNAME + "/livehelp", "0"])
    Orbited.connect(chat_event, nickname, ORBIT_HOSTNAME + "/livehelp", "0");
    request("/connect", {user:nickname, channel:CHANNEL});
    loggedOn = true;
  };
};

function chat() {
  msg = $('#chatbox_input').val();
  request("/msg", {to:"#" + CHANNEL,user:nickname,msg:msg});
  $('#chatbox_input').val('');
}

function quit() {
  request("/quit", {user:nickname})
}

function chat_event(data) {
  var type = data[0];
  var value = data[1];
  
  switch(type) {
    case 'ping': request("/ping_reply", {user:value}); break;
    case 'privmsg': privmsg(value[0], value[1], value[2]); break;
    case 'action': action(value[0], value[1], value[2]); break;
    case 'joined': joined(value[0]); break;
    case 'nickChanged': nickChanged(value); break;
    case 'userRenamed': userRenamed(value[0], value[1]); break;
    case 'userJoined':
      addName(value[0]);
      userJoined(value[0], value[1]);
      break;
    case 'userLeft':
      $(".user_list .user_entry#user" + value[0]).remove();
      userLeft(value[0], value[1], value[3]);
      break;
    case 'userQuit': userQuit(value[0], value[1]); break;
    case 'names': names(value[1]); break;
    case 'infomsg': infoMessage(value[0], value[1]); break;
  }
};

function nickChanged(newnick) {
    userRenamed(nickname, newnick);
    nickname = newnick;
}

function userRenamed(oldname, newname) {
  $("<div class='informative rename'></div>")
    .html("<span class='user'>" + oldname + "</span> is now known as " +
          "<span class='user'>" + newname + "</span>")
    .appendTo("#chathistory");
  scrollDown();

  $(".user_list .user#user" + oldname)
    .attr("id", "user" + newname)
    .html(newname);
}

function user_priviledges(name) {
  var privs_symbols = {"@":"admin", "%":"subadmin", "+":"voice"};
  if (name[0] in privs_symbols) {
    return privs_symbols[name[0]];
  } else {
    return "";
  };
};

function addName(name) {
  var priviledges = user_priviledges[name];
  users[name] = {"privs":priviledges};
  $('<div class="user_entry" id="user_' + name + '">' + name + '</div>')
    .addClass(priviledges)
    .appendTo("#user_list");
};

function removeName(name) {
  delete users[name];
  $(".user_list #user_" + name).remove()
};

function names(namelist) {
  for (var i = namelist.length - 1; i >= 0; i--){
    var name = namelist[i];
    if ($.trim(name) != "" & $(".user_list #user_" + name).length == 0) {
      addName(name);
    };
  };
  fillUserList();
};

function fillUserList() {
  $('.user_list').empty();
  //alert("test");
  var list = [];
  for (var user in users) {
    list.push(user);
  };
  list.sort()
  for (var i=0; i < list.length; i++) {
    var user = list[i];
    privs = users[user]['privs'];
    $('<div class="user_entry" id="user_' + user + '">' + user + '</div>')
      .addClass(privs)
      .appendTo("#user_list");
  };
};

function scrollDown() {
  var box = document.getElementById('chathistory');
  box.scrollTop = box.scrollHeight;
}

function isSubstring(sub, str) {
  // case insensitive substring test
  return str.toLowerCase().indexOf(sub.toLowerCase()) >= 0;
};

function sanitize(str) {
  return str.replace(/</, "&lt;").replace(/&/, '&amp;')
};

function privmsg(sender, message, channel) {
  if (channel != "#" + CHANNEL) {
    return false;
  };
  messagediv = $('<div class="message"></div>');
  if (sender == nickname) {
    messagediv.addClass("self");
  };
  if (isSubstring(nickname, message)) {
    messagediv.addClass("mentioned")
  };
  messagediv.html('<span class="user">' + sender + ':</span> ' +
                  colorize(sanitize(message)))
    .appendTo("#chathistory");
  scrollDown();
};

function action(sender, message, channel) {
  if (channel != CHANNEL) {
    return false;
  };
  messagediv = $('<div class="message action"></div>');
  if (sender == nickname) {
    messagediv.addClass("self");
  };
  if (isSubstring(nickname, message)) {
    messagediv.addClass("mentioned")
  };
  messagediv.html('<span class="user">• ' + sender + '</span> ' +
                  colorize(sanitize(message)))
    .appendTo("#chathistory");
  scrollDown();
};

function joined(joiner) {
  nickname = joiner;
  $("<div class='informative welcome'></div>")
    .html("Welcome to the " + CHANNEL + " channel.  Make yourself at home.")
    .appendTo("#chathistory");
  scrollDown();
};

function userJoined(joiner, channel) {
  addName(joiner);
  fillUserList();
  
  $("<div class='informative join'></div>")
    .html("<span class='user'>" + joiner + "</span> has joined " + CHANNEL)
    .appendTo("#chathistory");
  scrollDown();
};

function userLeft(leaver, channel, message) {
  $("<div class='informative part'></div>")
    .html("<span class='user'>" + leaver + "</span> " + message + CHANNEL)
    .appendTo("#chathistory");
  scrollDown();

  removeName(leaver);
};

function userQuit(quitter, message) {
  $("<div class='informative quit'></div>")
    .html("<span class='user'>" + quitter + "</span> quit (“" + message + "”)")
    .appendTo("#chathistory");
  scrollDown();
  
  removeName(quitter);
};

function infoMessage(message) {
  $("<div class='informative'></div>")
    .html(message)
    .appendTo("#chathistory");
  scrollDown();
};
