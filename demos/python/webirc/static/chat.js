top_domain = null
orbit_hostname = null
app_hostname = null
orig_domain = document.domain
nickname = null
currentChan = null
loggedOn = false

function astarta() {
    if (loggedOn) {
        var nick = document.getElementById('nickname').value
        add_request("/nick", {user:nickname,nickname:nick})
    }
    else {
        nickname = document.getElementById('nickname').value;
        e = document.getElementById('events');
        e.src=orbit_hostname + '/chat|' + nickname + ',0,iframe_domain';
        join();
    }
    document.getElementById('nickname').value = '[ENTER NICKNAME]';
}

function join() {
    add_request("/connect", {user:nickname})
    loggedOn = true
}

function joinChannel() {
    var channel = document.getElementById('channelfield')
    var channelval = channel.value.replace('#','')
    add_request("/join", {user:nickname,channel:channelval})
    channel.value = '[ENTER CHANNEL]'
}

function leaveChannel(channel) {
    channel = channel.replace('#','')
    add_request("/leave", {user:nickname,channel:channel})
    var chatfield = document.getElementById('chat')
    chatfield.focus()
}

function chat() {
    var msg = document.getElementById('chat').value
    document.getElementById('chat').value = ''
    add_request("/msg", {to:currentChan,user:nickname,msg:msg})
}

function createXMLHttpRequest() {
    try { return new ActiveXObject("Msxml2.XMLHTTP"); } catch (e) {}
    try { return new ActiveXObject("Microsoft.XMLHTTP"); } catch (e) {}
    try { return new XMLHttpRequest(); } catch(e) {}
    return null;
}

function make_query_string(params) {
    out = "?"
    for (var key in params) {
        out = out + key + '=' + escape(params[key]) + '&'
    }
    /* Get rid of trailing & */
    return out.substring(0, out.length-1);
}

function add_request(url, params) {
    document.domain = orig_domain
    xmlhttp = createXMLHttpRequest();
    xmlhttp.open("GET", app_hostname + url + make_query_string(params), true)
    xmlhttp.send(null);
    document.domain = top_domain
}

/*
function add_request(url,params) {
    document.domain = orig_domain
	x = doSimpleXMLHttpRequest(app_hostname + url, params)
    alert(x);
    document.domain = top_domain
}
*/
function event(data) {
    switch(data[0]) {
      case 'privmsg': privmsg(data[1]); break;
      case 'joined': joined(data[1]); break;
      case 'nickChanged': nickChanged(data[1]); break;
      case 'userRenamed': userRenamed(data[1]); break;
      case 'userJoined':
        addName(data[1]);
        userJoined(data[1]);
        break;
      case 'userLeft':
        removeName([data[1][0],document.getElementById(data[1][1]+'names')])
        userLeft(data[1])
        break;
      case 'userQuit': userQuit(data[1]); break;
      case 'ping': ping(data[1]); break;
      case 'names':
        names(data[1]);
        switchChannel(data[1][0]);
        break;
    }
}

function userRenamed([oldname,newname]) {
    if (document.getElementById('authtext') == null) {
        addChannel('auth')
    }
    chat_box = document.getElementById('authtext')
    div = document.createElement('div')
    div.className = "left"
    sender = document.createElement('span')
    sender.className = "sender"
    sender.innerHTML = oldname
    linker = document.createElement('span')
    linker.innerHTML = 'is now known as '
    sender2 = document.createElement('span')
    sender2.className = "sender"
    sender2.innerHTML = newname
    div.appendChild(sender)
    div.appendChild(linker)
    div.appendChild(sender2)
    chat_box.appendChild(div)
    if (currentChan == 'auth') {
        box = document.getElementById('box')
        box.scrollTop = box.scrollHeight
    }
    side = document.getElementById('side')
    for (i = 0; i < side.childNodes.length; i++) {
        for (z = 0; z < side.childNodes[i].childNodes.length; z++) {
            item = side.childNodes[i].childNodes[z]
            item.innerHTML = item.innerHTML.replace(
                '\''+oldname+'\')">@'+oldname+'</a>',
                '\''+newname+'\')">@'+newname+'</a>'
            ).replace(
                '\''+oldname+'\')">%'+oldname+'</a>',
                '\''+newname+'\')">%'+newname+'</a>'
            ).replace(
                '\''+oldname+'\')">+'+oldname+'</a>',
                '\''+newname+'\')">+'+newname+'</a>'
            ).replace(
                '\''+oldname+'\')">'+oldname+'</a>',
                '\''+newname+'\')">'+newname+'</a>'
            );
        }
    }
}

function nickChanged(newnick) {
    userRenamed([nickname, newnick])
    nickname = newnick
    e = document.getElementById('events');
    e.replace('/chat|' + nickname);
}

function userQuit([name,message]) {
    side = document.getElementById('side')
    for (i = 0; i < side.childNodes.length; i++) {
        removeName([name,side.childNodes[i]])
    }
    if (document.getElementById('authtext') == null) {
        addChannel('auth')
    }
    chat_box = document.getElementById('authtext')
    div = document.createElement('div')
    div.className = "left"
    sender = document.createElement('span')
    sender.className = "sender"
    sender.innerHTML = name
    linker = document.createElement('span')
    linker.innerHTML = message
    div.appendChild(sender)
    div.appendChild(linker)
    chat_box.appendChild(div)
    if (currentChan == 'auth') {
        box = document.getElementById('box')
        box.scrollTop = box.scrollHeight
    }
}

function removeName([name,cluster]) {
    for (z = 0; z < cluster.childNodes.length; z++) {
        item = cluster.childNodes[z]
        item.innerHTML = item.innerHTML.replace(
            '<a href="javascript:addChannel(\''+name+'\')">@'+name+'</a>',''
        ).replace(
            '<a href="javascript:addChannel(\''+name+'\')">%'+name+'</a>',''
        ).replace(
          '<a href="javascript:addChannel(\''+name+'\')">+'+name+'</a>',''
        ).replace(
          '<a href="javascript:addChannel(\''+name+'\')">'+name+'</a>',''
        )
    }
}

function addName(data) {
    if (data[0][0] == '@') {
        side = document.getElementById(data[1]+'admins')
        side.innerHTML = side.innerHTML + '<a href="javascript:addChannel(\''+data[0].replace('@','')+'\')">'+data[0]+'</a>'
    }
    else if (data[0][0] == '%') {
        side = document.getElementById(data[1]+'subadmins')
        side.innerHTML = side.innerHTML + '<a href="javascript:addChannel(\''+data[0].replace('%','')+'\')">'+data[0]+'</a>'
    }
    else if (data[0][0] == '+') {
        side = document.getElementById(data[1]+'voices')
        side.innerHTML = side.innerHTML + '<a href="javascript:addChannel(\''+data[0].replace('+','')+'\')">'+data[0]+'</a>'
    }
    else {
        side = document.getElementById(data[1]+'people')
        side.innerHTML = side.innerHTML + '<a href="javascript:addChannel(\''+data[0]+'\')">'+data[0]+'</a>'
    }
}

function switchChannel(channel) {
    if (currentChan != null) {
        oldnames = document.getElementById(currentChan+'names')
        oldtext = document.getElementById(currentChan+'text')
        oldnames.style.display = 'none'
        oldtext.style.display = 'none'
        document.getElementById(currentChan+'shortcut').style.fontSize = '100%'
        document.getElementById(currentChan+'shortcut').href = "javascript:switchChannel(\'"+currentChan+"\')"
    }
    newnames = document.getElementById(channel+'names')
    newtext = document.getElementById(channel+'text')
    box = document.getElementById('box')
    newnames.style.display = 'block'
    newtext.style.display = 'block'
    box.scrollTop = box.scrollHeight
    document.getElementById(channel+'shortcut').style.fontSize = '120%'
    document.getElementById(channel+'shortcut').href = "javascript:removeChannel(\'"+channel+"\')"
    currentChan = channel
    chatfield = document.getElementById('chat')
    chatfield.focus()
}

function addChannel(channel) {
    channelbar = document.getElementById('channel')
    if (channelbar.innerHTML.search('>'+channel+'</a>') != -1) {
        return switchChannel(channel)
    }
    channelbar.innerHTML += '<a id='+channel+'shortcut style="font-size: 100%;" href="javascript:switchChannel(\''+channel+'\')">'+channel+'</a>'
    channeltext = document.createElement('div')
    channeltext.className = 'channeltext'
    channeltext.id = channel + 'text'
    chat_box = document.getElementById('box')
    chat_box.appendChild(channeltext)
    admins = document.createElement('div')
    admins.className = 'admins'
    admins.id = channel+'admins'
    subadmins = document.createElement('div')
    subadmins.className = 'subadmins'
    subadmins.id = channel+'subadmins'
    voices = document.createElement('div')
    voices.className = 'voices'
    voices.id = channel+'voices'
    people = document.createElement('div')
    people.className = 'people'
    people.id = channel+'people'
    channelnames = document.createElement('div')
    channelnames.className = 'channelnames'
    channelnames.id = channel+'names'
    channelnames.appendChild(admins)
    channelnames.appendChild(subadmins)
    channelnames.appendChild(voices)
    channelnames.appendChild(people)
    side = document.getElementById('side')
    side.appendChild(channelnames)
}

function removeChannel(channel) {
    channelbar = document.getElementById('channel')
    channelbar.innerHTML = channelbar.innerHTML.replace('<a id=\"'+channel+'shortcut\" style="font-size: 120%;" href="javascript:removeChannel(\''+channel+'\')">'+channel+'</a>','')
    chat_box = document.getElementById('box')
    chat_box.removeChild(document.getElementById(channel+'text'))
    side = document.getElementById('side')
    side.removeChild(document.getElementById(channel+'names'))
    currentChan = null
    leaveChannel(channel)
    chatfield = document.getElementById('chat')
    chatfield.focus()
}

function names(data) {
    adminstring = ''
    subadminstring = ''
    voicesstring = ''
    peoplestring = ''
    for (i = 0; i < data[1].length; i++) {
        if (data[1][i][0] == '@') {
            adminstring += '<a href="javascript:addChannel(\''+data[1][i].replace('@','')+'\')">'+data[1][i]+'</a>'
        }
        else if (data[1][i][0] == '%') {
            subadminstring += '<a href="javascript:addChannel(\''+data[1][i].replace('%','')+'\')">'+data[1][i]+'</a>'
        }
        else if (data[1][i][0] == '+') {
            voicesstring += '<a href="javascript:addChannel(\''+data[1][i].replace('+','')+'\')">'+data[1][i]+'</a>'
        }
        else {
            peoplestring += '<a href="javascript:addChannel(\''+data[1][i]+'\')">'+data[1][i]+'</a>'
        }
    }
    admins = document.getElementById(data[0]+'admins')
    subadmins = document.getElementById(data[0]+'subadmins')
    voices = document.getElementById(data[0]+'voices')
    people = document.getElementById(data[0]+'people')
    admins.innerHTML = adminstring
    subadmins.innerHTML = subadminstring
    voices.innerHTML = voicesstring
    people.innerHTML = peoplestring
}

function ping(data) {
    var url = "/ping_reply"
    var params = {user:data}
    add_request(url,params)
}

function privmsg(data) {
    if (document.getElementById(data[2]+'text') == null) {
        addChannel(data[2])
    }
    chat_box = document.getElementById(data[2]+'text')
    div = document.createElement('div')
    div.className = "event"
    sender = document.createElement('span')
    sender.className = "sender"
    sender.innerHTML = data[0]
    message = document.createElement('span')
    message.className = "message"
    message.innerHTML = colorize(data[1])
    div.appendChild(sender)
    div.appendChild(message)
    chat_box.appendChild(div)
    if (currentChan == data[2]) {
        box = document.getElementById('box')
        box.scrollTop = box.scrollHeight
    }
}

function joined(data) {
    addChannel(data[1])
    chat_box = document.getElementById(data[1]+'text')
    div = document.createElement('div')
    div.className = "joined"
    sender = document.createElement('span')
    sender.className = "sender"
    sender.innerHTML = data[0]
    message = document.createElement('span')
    message.className = "message"
    message.innerHTML = data[1]
    linker = document.createElement('span')
    linker.innerHTML = 'has joined'
    div.appendChild(sender)
    div.appendChild(linker)
    div.appendChild(message)
    chat_box.appendChild(div)
    if (currentChan == data[1]) {
        box = document.getElementById('box')
        box.scrollTop = box.scrollHeight
    }
}

function userJoined(data) {
    chat_box = document.getElementById(data[1]+'text')
    div = document.createElement('div')
    div.className = "joined"
    sender = document.createElement('span')
    sender.className = "sender"
    sender.innerHTML = data[0]
    message = document.createElement('span')
    message.className = "message"
    message.innerHTML = data[1]
    linker = document.createElement('span')
    linker.innerHTML = 'has joined'
    div.appendChild(sender)
    div.appendChild(linker)
    div.appendChild(message)
    chat_box.appendChild(div)
    if (currentChan == data[1]) {
        box = document.getElementById('box')
        box.scrollTop = box.scrollHeight
    }
}

function userLeft(data) {
    chat_box = document.getElementById(data[1]+'text')
    div = document.createElement('div')
    div.className = "left"
    sender = document.createElement('span')
    sender.className = "sender"
    sender.innerHTML = data[0]
    message = document.createElement('span')
    message.className = "message"
    message.innerHTML = data[1]
    linker = document.createElement('span')
    linker.innerHTML = data[2]
    div.appendChild(sender)
    div.appendChild(linker)
    div.appendChild(message)
    chat_box.appendChild(div)
    if (currentChan == data[1]) {
        box = document.getElementById('box')
        box.scrollTop = box.scrollHeight
    }
}
