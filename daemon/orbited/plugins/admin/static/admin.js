recent_stats = {'plugins':{},'sessions':{},'all':{}};
current_stats = {'plugins':{},'sessions':{},'all':{}};
item_visible = {};
plugin_status = {};
history_length = 10;
graph_x = 600;
graph_y = 100;
x_size = graph_x/history_length;

function initialize() {
    init_graph(['users','msgs','bandwidth']);
    table = {'plugins':document.getElementById('plugins'),'sessions':document.getElementById('sessions')}
    recent_stats['all'] = make_full_dict();
}

function init_graph(names) {
    graph = {};
    for (name in names) {
        graph[names[name]] = {};
        graph[names[name]]['graph'] = document.getElementById('graph_'+names[name]).getContext('2d');
        graph[names[name]]['label'] = document.getElementById(names[name]+'_div');
    }
}

function on_off(id) {
    var x = document.getElementById(id);
    if (item_visible[id] == 'block') {
        item_visible[id] = 'none';
    }
    else {
        item_visible[id] = 'block';
    }
    document.getElementById(id).style.display = item_visible[id];
}

function final_link(type,name) {
    if (type == 'plugins') {
        return '<a href=/_/'+name+'/manage/ target=_blank>manage</a><br>';
    }
    // TERMINATE for sessions
}

function start_stop(name) {
    get('/_/'+name+'/manage/'+plugin_status[name],{}).success = function(result) {
        if (plugin_status[name] == 'start') {
            plugin_status[name] = 'stop';
        }
        else {
            plugin_status[name] = 'start';
        }
    }
}

function render_table_type(type) {
    table[type].innerHTML = '';
    for (plugin in recent_stats[type]) {
        table[type].innerHTML += '<a href=javascript:on_off("'+type+plugin+'");>'+plugin+'</a>';
        info = document.createElement('div');
        info.className = 'plugin_info';
        info.id = type+plugin;
        info.style.display = item_visible[type+plugin];
        info.innerHTML = '';
        for (attribute in recent_stats[type][plugin]) {
            info.innerHTML += attribute+': <b>'+recent_stats[type][plugin][attribute][history_length-1]+'</b> ';
        }
        if (type == 'plugins') {
            info.innerHTML += "<br><a href=# onClick=start_stop('"+plugin+"');>"+plugin_status[plugin]+"</a>";
        }
        info.innerHTML += "<br>"+final_link(type,plugin);
        table[type].appendChild(info);
    }
}

function render_tables() {
    render_table_type('plugins');
    render_table_type('sessions');
}

function render_graph() {
    for (attribute in recent_stats['all']) {
        graph[attribute]['graph'].clearRect(0,0,graph_x,graph_y);
        graph[attribute]['graph'].beginPath();
        graph[attribute]['graph'].moveTo(graph_x, graph_y - recent_stats['all'][attribute][0]);
        for (var x = 1; x < history_length; x++) {
            var a = x*x_size;
            var b = graph_y - recent_stats['all'][attribute][x];
            graph[attribute]['graph'].lineTo(a,b);
        }
        graph[attribute]['graph'].stroke();
        graph[attribute]['label'].innerHTML = attribute+"<br><b>"+current_stats['all'][attribute]+"</b>"
    }
}

function render() {
    render_tables();
    render_graph();
}

function make_history_list() {
    var the_list = [];
    for (var x = 0; x < history_length; x++) {
        the_list[x] = 0;
    }
    return the_list;
}

function make_full_dict() {
    return {'bandwidth':make_history_list(),'msgs':make_history_list(),'users':make_history_list()}
}

function set_plugin_status(plugin) {
    get('/_/'+plugin+'/manage/status',{}).success = function(result) {
        if (result[1] == "Plugin is running") {
            plugin_status[plugin] = 'stop';
        }
        else {
            plugin_status[plugin] = 'start';
        }
    }
}

function update_type(data,type) {
    clear_stats(type);
    for (plugin in data) {
        if (! (plugin in recent_stats[type])) {
            recent_stats[type][plugin] = make_full_dict();
            item_visible[type+plugin] = 'none';
            if (type == 'plugins') {
                set_plugin_status(plugin);
            }
        }
        for (attribute in data[plugin]) {
            recent_stats[type][plugin][attribute].shift();
            recent_stats[type][plugin][attribute].push(data[plugin][attribute]);
            current_stats[type][attribute] += data[plugin][attribute];
            current_stats['all'][attribute] += data[plugin][attribute];
        }
        if (recent_stats[type][plugin]['users'] == 0) {
            recent_stats[type][plugin] = null;
        }
    }
}

function update_recent_all() {
    for (attribute in current_stats['all']) {
        recent_stats['all'][attribute].shift();
        recent_stats['all'][attribute].push(current_stats['all'][attribute]);
    }
}

function clear_stats(type) {
    current_stats[type]['bandwidth'] = 0;
    current_stats[type]['msgs'] = 0;
    current_stats[type]['users'] = 0;
}

function update(data) {
    clear_stats('all');
    clear_stats('plugins');
    clear_stats('sessions');
    update_type(data['plugins'],'plugins');
    update_type(data['sessions'],'sessions');
    update_recent_all();
}

function receive_event(data) {
    update(data);
    render();
}
