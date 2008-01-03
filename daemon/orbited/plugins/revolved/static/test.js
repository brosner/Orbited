
function startup(server, port, user) {
    Revolved.connect(server, port, 'test_resource').success = function() {
        Revolved.subscribe("hello", eventcb);
        Revolved.publish("hello", "good day");
        Revolved.authenticate(user, "").success = function() {
            Revolved.publish("hello", "still here?");
            Revolved.authenticate("jacob", "yohoho").success = function() {
                Revolved.publish("hello", "it's me!");
            }
        }
    }
}

function eventcb(channel, sender, message) {
    console.log([channel, sender, message]);
}