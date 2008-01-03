var foodiv = null;
function do_connect() {
    foodiv = document.getElementById('foo')
//    alert('mofo');
    function got_event(event) {
            document.getElementById('foo').innerHTML = event
//            document.getElementById('foo').innerHTML = event
//            document.getElementById('foo').innerHTML = event
//            document.getElementById('foo').innerHTML = event


//11, 14, 17, 24, 42            
//            foodiv.innerHTML = event
//            foodiv.innerHTML = event
//        alert(event);
    }
    Orbited.connect(got_event, "alerter", "/event", "0", "htmlfile");
    alert('doneo');
}