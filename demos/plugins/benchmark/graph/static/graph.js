var mem = [];
var cpu = [];
var graph_height = 350.0;
var graph_width = 400.0;
var y_buffer = 50.0
var x_size = 30;
var y_size = (graph_height-y_buffer)/100;

function connect() {
    setup();
    Orbited.connect(graph_event, user, "/_/graph/event", "0");
}

function setup() {
    for (var x = 0; x < x_size; x++) {
        mem[x] = 0;
        cpu[x] = 0;
    }
    ctx = document.getElementById('mario').getContext('2d');
    ctx.lineJoin = 'round';
    user = 'admin'+Math.round(10000*Math.random());
}

function render() {
    ctx.clearRect(0,0,graph_width+1,graph_height+1);

    ctx.beginPath();
    ctx.moveTo(0,graph_height-(cpu[0]*y_size));
    for (var x = 1; x < x_size; x++) {
        var a = x*graph_width/x_size;
        var b = graph_height-(cpu[x]*y_size);
        ctx.lineTo(a,b);
    }
    ctx.lineWidth = 3;
    ctx.strokeStyle = 'rgba(85,26,81,1)';
    ctx.stroke();
    ctx.lineWidth = .8;
    ctx.strokeStyle = 'rgba(255,255,255,1)';
    ctx.stroke();

    ctx.beginPath();
    ctx.moveTo(0,graph_height-(mem[0]*y_size));
    for (var x = 1; x < x_size; x++) {
        var a = x*graph_width/x_size;
        var b = graph_height-(mem[x]*y_size);
        ctx.lineTo(a,b);
    }
    ctx.lineWidth = 3;
    ctx.strokeStyle = 'rgba(0,62,18,1)';
    ctx.stroke();
    ctx.lineWidth = .8;
    ctx.strokeStyle = 'rgba(255,255,255,1)';
    ctx.stroke();
}

function update(data) {
    cpu.shift();
    cpu.push(data[0]);
    mem.shift();
    mem.push(data[1]);
}

function graph_event(data) {
    update(data);
    render();
}
